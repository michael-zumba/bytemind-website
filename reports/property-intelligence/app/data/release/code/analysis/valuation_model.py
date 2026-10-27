"""Calibrated hedonic fallback model for listings without a Homes AVM.

The primary external valuation is Homes.co.nz's AVM (extracted from Trade Me). This
module adds a transparent, testable model for the ~50% of listings where Homes has no
match:

- Train on listings that do have an AVM, using structural, location, tenure, sale-method
  and (when available) description/topic features.
- Validate with 5-fold cross-validation against a suburb-median baseline.
- Produce an 80% prediction interval from out-of-fold residuals, then predict every
  listing. The model is a fallback/cross-check, not a replacement for the Homes AVM.

A separate model checks whether description text adds predictive power. A sale-price
model trained on nearby sold records provides an independent cross-check.
"""
from __future__ import annotations

import json
import math
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, r2_score
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

MODEL_VERSION = "hedonic-avm-v1"
SEED = 42
N_FOLDS = 5


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load(conn: sqlite3.Connection) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    conn.row_factory = sqlite3.Row
    df = pd.read_sql_query(
        """SELECT * FROM listings WHERE is_standard=1 ORDER BY id""", conn
    )
    sales = pd.read_sql_query(
        """SELECT * FROM sales WHERE sale_price > 0 AND cv > 0""", conn
    )
    try:
        school_counts = pd.read_sql_query(
            """SELECT l.id AS listing_id, COUNT(lss.school_id) AS in_zone_schools
               FROM listings l
               LEFT JOIN listing_schools lss ON lss.listing_id=l.id AND lss.in_zone=1
               GROUP BY l.id""",
            conn,
        )
    except sqlite3.Error:
        school_counts = pd.DataFrame(columns=["listing_id", "in_zone_schools"])
    df = df.merge(school_counts, left_on="id", right_on="listing_id", how="left")
    df["in_zone_schools"] = df["in_zone_schools"].fillna(0)
    return df, sales, school_counts


def _text_frame(conn: sqlite3.Connection) -> pd.DataFrame:
    """Join whatever text features the text_model module has produced."""
    try:
        tf = pd.read_sql_query("SELECT * FROM text_features", conn)
    except (sqlite3.Error, pd.errors.DatabaseError):
        return pd.DataFrame()
    if tf.empty:
        return pd.DataFrame()
    rename = {
        "urgency": "urgency_score",
        "luxury": "luxury_score",
        "condition_renovation": "condition_score",
        "views_waterfront": "views_score",
        "family_school": "family_score",
        "investment": "investment_score",
        "risk": "risk_score",
        "exclamations": "exclamation_count",
        "description_premium_pct": "description_premium",
    }
    tf = tf.rename(columns=rename)
    keep = [
        c for c in tf.columns
        if c in {
            "listing_id", "description_index", "description_premium",
            "urgency_score", "luxury_score", "condition_score", "risk_score",
            "family_score", "views_score", "investment_score", "word_count",
            "exclamation_count",
        }
    ]
    tf = tf[keep].copy()
    try:
        topics = pd.read_sql_query(
            "SELECT listing_id, topic_id, weight FROM listing_topics", conn
        )
        if not topics.empty:
            pivot = topics.pivot(index="listing_id", columns="topic_id", values="weight")
            pivot.columns = [f"topic_{c}" for c in pivot.columns]
            tf = tf.merge(pivot.reset_index(), on="listing_id", how="left")
    except (sqlite3.Error, pd.errors.DatabaseError):
        pass
    tf = tf.rename(columns={"listing_id": "id"})
    return tf


def _stage(conn: sqlite3.Connection, df: pd.DataFrame) -> pd.DataFrame:
    if "sale_method_stage" in df.columns and df["sale_method_stage"].notna().any():
        return df
    from analysis.sale_method import stage_for
    df["sale_method_stage"] = df.apply(
        lambda r: stage_for(r.get("sale_method"), r.get("asking_kind")), axis=1
    )
    return df


def _add_engineered(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ("cv", "land_area", "floor_area", "bedrooms", "bathrooms", "parking",
                "lounges", "days_on_market", "sale_method_stage", "in_zone_schools"):
        out[col] = pd.to_numeric(out.get(col), errors="coerce")
    out["cv_log"] = np.log(out["cv"].where(out["cv"] > 0))
    out["land_log"] = np.log1p(out["land_area"].clip(lower=0))
    out["floor_log"] = np.log1p(out["floor_area"].clip(lower=0))
    out["build_year"] = pd.to_numeric(out.get("build_decade"), errors="coerce")
    out["has_cv"] = out["cv"].notna().astype(int)
    out["has_land"] = out["land_area"].notna().astype(int)
    out["has_floor"] = out["floor_area"].notna().astype(int)
    return out


def _feature_spec(df: pd.DataFrame, text: bool, include_cv: bool = True) -> tuple[list[str], list[str], list[str]]:
    numeric = [
        "bedrooms", "bathrooms", "parking", "lounges",
        "land_log", "floor_log", "build_year", "days_on_market",
        "sale_method_stage", "in_zone_schools",
        "has_land", "has_floor",
    ]
    if include_cv:
        numeric[:0] = ["cv_log", "has_cv"]
    categorical = ["suburb_name", "property_type", "tenure", "sale_method"]
    text_cols = [
        c for c in df.columns
        if c in {
            "description_index", "description_premium", "urgency_score", "luxury_score",
            "condition_score", "risk_score", "family_score", "views_score",
            "investment_score", "word_count", "exclamation_count",
        } or c.startswith("topic_")
    ]
    numeric = [c for c in numeric if c in df.columns]
    categorical = [c for c in categorical if c in df.columns]
    if text:
        numeric += [c for c in text_cols if c not in numeric]
    return numeric, categorical, text_cols


def _pipeline(numeric: list[str], categorical: list[str]) -> Pipeline:
    pre = ColumnTransformer(
        [
            ("num", Pipeline([
                ("impute", SimpleImputer(strategy="median", add_indicator=False)),
                ("scale", StandardScaler()),
            ]), numeric),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
        ],
        remainder="drop",
    )
    return Pipeline([("pre", pre), ("ridge", Ridge(alpha=10.0, random_state=SEED))])


def _metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    return {
        "r2": round(float(r2_score(y_true, y_pred)), 4),
        "mae": round(float(mean_absolute_error(np.exp(y_true), np.exp(y_pred))), 1),
        "mape": round(float(mean_absolute_percentage_error(np.exp(y_true), np.exp(y_pred))), 4),
        "median_ape": round(float(np.median(np.abs(np.exp(y_true) - np.exp(y_pred)) / np.exp(y_true))), 4),
    }


def _active_guide_baseline(df: pd.DataFrame, train_idx: np.ndarray, test_idx: np.ndarray) -> np.ndarray:
    train = df.iloc[train_idx]
    preds = []
    for _, row in df.iloc[test_idx].iterrows():
        candidates = train[
            (train["suburb_name"] == row["suburb_name"])
            & (train["property_type"] == row["property_type"])
            & (train["bedrooms"].between((row["bedrooms"] or 0) - 1, (row["bedrooms"] or 0) + 1))
        ]
        if len(candidates) < 3:
            candidates = train[
                (train["suburb_name"] == row["suburb_name"])
                & (train["property_type"] == row["property_type"])
            ]
        if len(candidates) < 3:
            candidates = train[train["suburb_name"] == row["suburb_name"]]
        preds.append(float(candidates["estimate_mid"].median()) if len(candidates) else float(train["estimate_mid"].median()))
    return np.array(preds)


def _fit_and_validate(df: pd.DataFrame, text: bool, include_cv: bool = True) -> dict[str, Any]:
    train = df[df["estimate_mid"].notna()].copy()
    y = np.log(train["estimate_mid"].astype(float)).to_numpy()
    numeric, categorical, text_cols = _feature_spec(train, text, include_cv=include_cv)
    model = _pipeline(numeric, categorical)
    kf = KFold(N_FOLDS, shuffle=True, random_state=SEED)
    folds = list(kf.split(train))
    oof = np.zeros(len(train))
    baseline = np.zeros(len(train))
    for train_idx, test_idx in folds:
        fold_model = _pipeline(numeric, categorical)
        fold_model.fit(train.iloc[train_idx], y[train_idx])
        oof[test_idx] = fold_model.predict(train.iloc[test_idx])
        baseline[test_idx] = _active_guide_baseline(train, train_idx, test_idx)
    residual = y - oof
    return {
        "train": train,
        "model": model.fit(train, y),
        "numeric": numeric,
        "categorical": categorical,
        "text_cols": text_cols,
        "folds": folds,
        "oof": oof,
        "baseline": baseline,
        "y": y,
        "residual": residual,
        "metrics": _metrics(y, oof),
        "baseline_metrics": _metrics(y, np.log(baseline)),
        "interval_low": float(np.quantile(residual, 0.10)),
        "interval_high": float(np.quantile(residual, 0.90)),
        "coverage": float(np.mean((y >= oof + np.quantile(residual, 0.10))
                                  & (y <= oof + np.quantile(residual, 0.90)))),
    }


def _predict_frame(model: Pipeline, df: pd.DataFrame, numeric: list[str], categorical: list[str],
                   interval_low: float, interval_high: float) -> pd.DataFrame:
    pred = model.predict(df)
    rows = []
    for i, (_, row) in enumerate(df.iterrows()):
        mid = float(np.exp(pred[i]))
        low = float(np.exp(pred[i] + interval_low))
        high = float(np.exp(pred[i] + interval_high))
        rel_width = (high - low) / mid if mid else 1.0
        if rel_width <= 0.22 and row.get("has_cv", 0) and (row.get("has_land", 0) or row.get("has_floor", 0)):
            confidence = "high"
        elif rel_width <= 0.40:
            confidence = "medium"
        else:
            confidence = "low"
        rows.append({
            "listing_id": int(row["id"]),
            "low": int(round(low)),
            "mid": int(round(mid)),
            "high": int(round(high)),
            "confidence": confidence,
            "rel_width": round(rel_width, 4),
        })
    return pd.DataFrame(rows)


def _sale_model(conn: sqlite3.Connection, listings: pd.DataFrame) -> dict[str, Any]:
    sales = pd.read_sql_query(
        """SELECT sale_price, cv, bedrooms, bathrooms, suburb, lat, lon, sale_date
           FROM sales WHERE sale_price > 0 AND cv > 0""", conn
    )
    if len(sales) < 80:
        return {"n": len(sales), "note": "too few sold records"}
    sales["cv_log"] = np.log(sales["cv"].astype(float))
    sales["beds"] = pd.to_numeric(sales["bedrooms"], errors="coerce").fillna(3)
    sales["baths"] = pd.to_numeric(sales["bathrooms"], errors="coerce").fillna(1)
    sales["lat"] = pd.to_numeric(sales["lat"], errors="coerce")
    sales["lon"] = pd.to_numeric(sales["lon"], errors="coerce")
    sales["sale_month"] = pd.to_datetime(sales["sale_date"], errors="coerce").dt.year * 12 + pd.to_datetime(sales["sale_date"], errors="coerce").dt.month
    sales["sale_month"] = sales["sale_month"].fillna(sales["sale_month"].median())
    numeric = ["cv_log", "beds", "baths", "lat", "lon", "sale_month"]
    categorical = ["suburb"]
    y = np.log(sales["sale_price"].astype(float)).to_numpy()
    model = _pipeline(numeric, categorical)
    kf = KFold(5, shuffle=True, random_state=SEED)
    oof = cross_val_predict(model, sales, y, cv=kf)
    model.fit(sales, y)
    # Predict only for listings with an actual CV (the feature is required).
    target = listings[listings["cv"].notna() & (listings["cv"] > 0)].copy()
    target["suburb"] = target["suburb_name"]
    target["cv_log"] = np.log(target["cv"].astype(float))
    target["beds"] = pd.to_numeric(target["bedrooms"], errors="coerce").fillna(3)
    target["baths"] = pd.to_numeric(target["bathrooms"], errors="coerce").fillna(1)
    target["lat"] = pd.to_numeric(target["lat"], errors="coerce")
    target["lon"] = pd.to_numeric(target["lon"], errors="coerce")
    target["sale_month"] = pd.to_datetime(target["last_seen_at"], errors="coerce").dt.year * 12 + pd.to_datetime(target["last_seen_at"], errors="coerce").dt.month
    target["sale_month"] = target["sale_month"].fillna(sales["sale_month"].median())
    pred = model.predict(target)
    residual = y - oof
    q10, q90 = float(np.quantile(residual, 0.10)), float(np.quantile(residual, 0.90))
    rows = []
    for i, (_, row) in enumerate(target.iterrows()):
        raw = float(np.exp(pred[i]))
        rows.append({
            "listing_id": int(row["id"]),
            "low": int(round(float(np.exp(pred[i] + q10)))),
            "mid": int(round(raw)),
            "high": int(round(float(np.exp(pred[i] + q90)))),
            "confidence": "medium",
        })
    return {
        "n": len(sales),
        "metrics": _metrics(y, oof),
        "q10": q10,
        "q90": q90,
        "predictions": rows,
        "model_version": "sale-cv-v1",
    }


def run(conn: sqlite3.Connection, *, now_iso: str | None = None) -> dict[str, Any]:
    now_iso = now_iso or _now()
    df, sales, _ = _load(conn)
    df = _add_engineered(_stage(conn, df))
    text = _text_frame(conn)
    if not text.empty:
        df = df.merge(text, on="id", how="left")
    # Structural model (baseline and final model).
    structural = _fit_and_validate(df, text=False)
    metrics = {
        "n_train": int(len(structural["train"])),
        "n_listings": int(len(df)),
        "structural": structural["metrics"],
        "baseline_active_guide": structural["baseline_metrics"],
        "interval_low": round(structural["interval_low"], 4),
        "interval_high": round(structural["interval_high"], 4),
        "interval_coverage_80": round(structural["coverage"], 4),
        "model_version": MODEL_VERSION,
        "trained_at": now_iso,
        "features": len(structural["numeric"]) + len(structural["categorical"]),
    }
    no_cv = _fit_and_validate(df, text=not text.empty, include_cv=False)
    metrics["no_cv_model"] = {
        "metrics": no_cv["metrics"],
        "baseline_active_guide": no_cv["baseline_metrics"],
        "interval": [round(no_cv["interval_low"], 4), round(no_cv["interval_high"], 4)],
    }
    best = structural
    if not text.empty:
        text_model = _fit_and_validate(df, text=True)
        metrics["with_text"] = text_model["metrics"]
        metrics["text_delta"] = {
            "r2": round(text_model["metrics"]["r2"] - structural["metrics"]["r2"], 4),
            "mae": round(text_model["metrics"]["mae"] - structural["metrics"]["mae"], 1),
            "mape": round(text_model["metrics"]["mape"] - structural["metrics"]["mape"], 4),
        }
        if text_model["metrics"]["mae"] < structural["metrics"]["mae"]:
            best = text_model
            metrics["selected"] = "structural_plus_text"
        else:
            metrics["selected"] = "structural"
    else:
        metrics["selected"] = "structural"
        metrics["with_text"] = None
        metrics["text_delta"] = None

    # Predict every standard listing with the selected model. Listings without a CV
    # use the no-CV variant, which is calibrated only on listings where CV exists.
    preds = _predict_frame(
        best["model"], df, best["numeric"], best["categorical"],
        best["interval_low"], best["interval_high"],
    )
    no_cv_preds = _predict_frame(
        no_cv["model"], df, no_cv["numeric"], no_cv["categorical"],
        no_cv["interval_low"], no_cv["interval_high"],
    )
    pred_by_id = {int(r.listing_id): r for r in preds.itertuples()}
    no_cv_by_id = {int(r.listing_id): r for r in no_cv_preds.itertuples()}
    final_rows = []
    for _, row in df.iterrows():
        lid = int(row["id"])
        picked = pred_by_id[lid] if int(row.get("has_cv") or 0) == 1 else no_cv_by_id[lid]
        variant = "with_cv" if int(row.get("has_cv") or 0) == 1 else "no_cv"
        interval = (
            (best["interval_low"], best["interval_high"])
            if variant == "with_cv" else (no_cv["interval_low"], no_cv["interval_high"])
        )
        final_rows.append({
            "listing_id": lid, "low": picked.low, "mid": picked.mid, "high": picked.high,
            "confidence": picked.confidence, "rel_width": picked.rel_width, "variant": variant,
            "interval_low": round(interval[0], 4), "interval_high": round(interval[1], 4),
        })
    import pandas as _pd
    preds = _pd.DataFrame(final_rows)
    conn.executemany(
        """INSERT INTO model_predictions
           (listing_id, model_name, low, mid, high, confidence, basis_json, created_at)
           VALUES (?,?,?,?,?,?,?,?)
           ON CONFLICT(listing_id, model_name) DO UPDATE SET
             low=excluded.low, mid=excluded.mid, high=excluded.high,
             confidence=excluded.confidence, basis_json=excluded.basis_json,
             created_at=excluded.created_at""",
        [
            (
                int(r.listing_id), "hedonic_avm", int(r.low), int(r.mid), int(r.high),
                r.confidence,
                json.dumps({
                    "model_version": MODEL_VERSION,
                    "interval": [r.interval_low, r.interval_high],
                    "rel_width": r.rel_width,
                    "selected": metrics["selected"],
                    "variant": r.variant,
                }),
                now_iso,
            )
            for r in preds.itertuples()
        ],
    )
    # Use the hedonic model only as a fallback when no comp/AVM exists.
    for row in preds.itertuples():
        conn.execute(
            """UPDATE listings SET
                 value_low=?, value_mid=?, value_high=?, value_source='hedonic_avm',
                 value_confidence=?
               WHERE id=? AND value_source='active_suburb_guide'
                 AND ? IN ('high','medium')""",
            (int(row.low), int(row.mid), int(row.high), row.confidence, int(row.listing_id),
             row.confidence),
        )

    try:
        sale = _sale_model(conn, df)
    except Exception as exc:  # noqa: BLE001 - auxiliary model must not break the AVM model
        sale = {"n": 0, "error": str(exc)[:500]}
    if sale.get("predictions"):
        conn.executemany(
            """INSERT INTO model_predictions
               (listing_id, model_name, low, mid, high, confidence, basis_json, created_at)
               VALUES (?,?,?,?,?,?,?,?)
               ON CONFLICT(listing_id, model_name) DO UPDATE SET
                 low=excluded.low, mid=excluded.mid, high=excluded.high,
                 confidence=excluded.confidence, basis_json=excluded.basis_json,
                 created_at=excluded.created_at""",
            [
                (
                    int(r["listing_id"]), "sale_cv", r["low"], r["mid"], r["high"],
                    r["confidence"],
                    json.dumps({"model_version": "sale-cv-v1", "n": sale["n"]}),
                    now_iso,
                )
                for r in sale["predictions"]
            ],
        )
    metrics["sale_model"] = {k: v for k, v in sale.items() if k != "predictions"}

    def save_metric(model_name: str, metric: str, value: Any, detail: Any = None) -> None:
        conn.execute(
            """INSERT INTO model_metrics (model_name, metric, value, detail_json, created_at)
               VALUES (?,?,?,?,?)
               ON CONFLICT(model_name, metric) DO UPDATE SET
                 value=excluded.value, detail_json=excluded.detail_json,
                 created_at=excluded.created_at""",
            (
                model_name, metric,
                float(value) if isinstance(value, (int, float)) else None,
                json.dumps(detail, ensure_ascii=False) if detail is not None else None,
                now_iso,
            ),
        )

    for key in ("r2", "mae", "mape", "median_ape"):
        save_metric("hedonic_avm", key, metrics["structural"].get(key), metrics["structural"])
    for key, value in metrics.items():
        if key in {"structural", "with_text", "baseline_active_guide", "sale_model"}:
            continue
        save_metric("hedonic_avm", f"meta_{key}", value if isinstance(value, (int, float)) else None,
                    value if not isinstance(value, (int, float)) else None)
    for key in ("r2", "mae", "mape", "median_ape"):
        save_metric("hedonic_no_cv", key, metrics["no_cv_model"]["metrics"].get(key), metrics["no_cv_model"]["metrics"])
    save_metric("hedonic_no_cv", "n_train", float(len(no_cv["train"])), None)
    save_metric("hedonic_no_cv", "meta_interval", None, metrics["no_cv_model"]["interval"])
    # Compare the existing comp model with the Homes AVM on AVM-backed listings.
    comp_rows = df[df["estimate_mid"].notna() & df["comp_mid"].notna()].copy()
    comp_metrics = {}
    if len(comp_rows) >= 20:
        comp_metrics = _metrics(
            np.log(comp_rows["estimate_mid"].astype(float).to_numpy()),
            np.log(comp_rows["comp_mid"].astype(float).to_numpy()),
        )
        comp_metrics["n"] = int(len(comp_rows))
        for key in ("r2", "mae", "mape", "median_ape"):
            save_metric("comp_model", key, comp_metrics.get(key), comp_metrics)
    save_metric("active_guide", "mae", metrics["baseline_active_guide"].get("mae"), metrics["baseline_active_guide"])
    save_metric("active_guide", "mape", metrics["baseline_active_guide"].get("mape"), metrics["baseline_active_guide"])
    if sale.get("metrics"):
        for key, value in sale["metrics"].items():
            save_metric("sale_cv", key, value, sale["metrics"])
    conn.commit()
    return {
        "model_version": MODEL_VERSION,
        "n_train": metrics["n_train"],
        "n_listings": metrics["n_listings"],
        "selected": metrics["selected"],
        "metrics": metrics,
        "predictions": len(preds),
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Train the hedonic fallback model")
    parser.add_argument("--db", default=str(Path(__file__).resolve().parent.parent / "data" / "auckland_property.db"))
    args = parser.parse_args()
    conn = sqlite3.connect(args.db)
    try:
        print(json.dumps(run(conn), indent=1)[:4000])
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
