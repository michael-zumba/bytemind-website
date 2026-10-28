"""Match realised sale prices back to prior listing estimates and recalibrate.

The feedback loop is deliberately conservative:

1. Match a Homes.co.nz ``property_sale`` record to the same property only when the
   sale date is on/after the listing's ``listed_at`` (or first observation).
2. Store the realised outcome with the estimate that existed for that listing.
3. Measure error and interval coverage against the prior value range.
4. Publish a rolling calibration factor by suburb/type/tenure. The factor is
   applied as a separate ``sale_feedback_v1`` signal; it never silently replaces
   the Homes AVM or comparable range.
5. If enough outcomes accumulate, an optional ridge model is fitted on the
   realised outcomes and stored as ``sale_feedback_ml`` for evaluation.

The layer runs inside every ``db.build`` after ``property_sales`` is refreshed.
Actual sale prices are therefore picked up on the next daily refresh automatically.
"""
from __future__ import annotations

import json
import math
import sqlite3
from datetime import datetime, timezone
from statistics import median
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

MODEL_VERSION = "sale-feedback-v1"
SEED = 42
MIN_CALIBRATION_N = 10
MIN_ML_N = 30


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _date_part(value: Any) -> str | None:
    if not value:
        return None
    return str(value)[:10]


def _days_between(later: Any, earlier: Any) -> float | None:
    try:
        a = datetime.fromisoformat(str(later).replace("Z", "+00:00"))
        b = datetime.fromisoformat(str(earlier).replace("Z", "+00:00"))
        return round((a - b).total_seconds() / 86400, 2)
    except (TypeError, ValueError):
        return None


def _json(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return value


def match_outcomes(conn: sqlite3.Connection, *, now_iso: str) -> int:
    """Rebuild listing_sale_outcomes from the current Homes sale record set."""
    conn.row_factory = sqlite3.Row
    conn.execute("DELETE FROM listing_sale_outcomes")
    listings = [
        dict(r) for r in conn.execute(
            """SELECT id, address, homes_property_id, listed_at, first_seen_at,
                      asking_price, estimate_low, estimate_mid, estimate_high,
                      value_low, value_mid, value_high, comp_mid, cv,
                      suburb_slug, suburb_name, property_type, bedrooms, bathrooms,
                      land_area, floor_area, build_year, build_decade, tenure,
                      sale_method, status
               FROM listings
               WHERE homes_property_id IS NOT NULL AND homes_property_id != ''"""
        )
    ]
    snapshots_by_listing: dict[int, list[dict[str, Any]]] = {}
    for row in conn.execute(
        """SELECT listing_id, captured_at, estimate_mid, value_mid
           FROM listing_snapshots ORDER BY listing_id, captured_at"""
    ):
        snapshots_by_listing.setdefault(int(row["listing_id"]), []).append(dict(row))
    estimate_by_listing: dict[int, list[dict[str, Any]]] = {}
    for row in conn.execute(
        """SELECT listing_id, date, estimate_low, estimate_mid, estimate_high
           FROM estimate_history ORDER BY listing_id, date"""
    ):
        estimate_by_listing.setdefault(int(row["listing_id"]), []).append(dict(row))
    sales_by_property: dict[str, list[dict[str, Any]]] = {}
    for row in conn.execute(
        """SELECT homes_property_id, sale_date, sale_price, display_price, source
           FROM property_sales
           WHERE sale_price IS NOT NULL AND sale_price > 0
           ORDER BY homes_property_id, sale_date"""
    ):
        sales_by_property.setdefault(str(row["homes_property_id"]), []).append(dict(row))

    inserted = 0
    for listing in listings:
        sale_rows = sales_by_property.get(str(listing["homes_property_id"]), [])
        if not sale_rows:
            continue
        start = _date_part(listing.get("listed_at") or listing.get("first_seen_at"))
        if not start:
            continue
        # Earliest sale on/after the listing start is the outcome of this campaign.
        candidates = [
            sale for sale in sale_rows
            if _date_part(sale.get("sale_date")) and _date_part(sale.get("sale_date")) >= start
        ]
        if not candidates:
            continue
        sale = candidates[0]
        sale_date = str(sale["sale_date"])
        price = int(sale["sale_price"])
        # The feedback must judge a pre-sale estimate, never today's refreshed
        # value. Prefer the Homes estimate history point immediately before the
        # sale; fall back to a pre-sale listing snapshot.
        prior_est = None
        for est in estimate_by_listing.get(int(listing["id"]), []):
            if _date_part(est.get("date")) and _date_part(est.get("date")) <= _date_part(sale_date):
                prior_est = est
        prior_snap = None
        for snap in snapshots_by_listing.get(int(listing["id"]), []):
            if _date_part(snap.get("captured_at")) and _date_part(snap.get("captured_at")) <= _date_part(sale_date):
                prior_snap = snap
        estimate_low = estimate_mid = estimate_high = None
        value_low = value_mid = value_high = None
        prediction_source = "unavailable_no_pre_sale_estimate"
        if prior_est and prior_est.get("estimate_mid"):
            estimate_low = prior_est.get("estimate_low")
            estimate_mid = prior_est.get("estimate_mid")
            estimate_high = prior_est.get("estimate_high")
            value_low, value_mid, value_high = estimate_low, estimate_mid, estimate_high
            prediction_source = "estimate_history_before_sale"
        elif prior_snap and (prior_snap.get("value_mid") or prior_snap.get("estimate_mid")):
            value_mid = prior_snap.get("value_mid") or prior_snap.get("estimate_mid")
            value_low = prior_snap.get("value_mid") and listing.get("value_low")
            value_high = prior_snap.get("value_mid") and listing.get("value_high")
            prediction_source = "snapshot_before_sale"
        error = int(price - value_mid) if value_mid else None
        abs_error = abs(error) if error is not None else None
        abs_pct = round(abs_error / value_mid, 6) if abs_error is not None and value_mid else None
        low, high = value_low, value_high
        within = (
            1 if low is not None and high is not None and low <= price <= high else
            0 if low is not None and high is not None else None
        )
        conn.execute(
            """INSERT OR IGNORE INTO listing_sale_outcomes (
                 listing_id, homes_property_id, sale_date, sale_price, sale_display,
                 listing_listed_at, listing_first_seen_at, asking_price,
                 estimate_low, estimate_mid, estimate_high, value_low, value_mid,
                 value_high, comp_mid, cv, suburb_slug, suburb_name, property_type,
                 bedrooms, bathrooms, land_area, floor_area, build_year, build_decade,
                 tenure, sale_method, days_listing_to_sale, prediction_error,
                 prediction_abs_error, prediction_abs_pct, within_80_interval,
                 prediction_source, source, matched_at
               ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                listing["id"], listing["homes_property_id"], sale_date, price,
                sale.get("display_price"), listing.get("listed_at"), listing.get("first_seen_at"),
                listing.get("asking_price"), estimate_low, estimate_mid, estimate_high,
                value_low, value_mid, value_high, listing.get("comp_mid"), listing.get("cv"),
                listing.get("suburb_slug"), listing.get("suburb_name"), listing.get("property_type"),
                listing.get("bedrooms"), listing.get("bathrooms"), listing.get("land_area"),
                listing.get("floor_area"), listing.get("build_year"), listing.get("build_decade"),
                listing.get("tenure"), listing.get("sale_method"),
                _days_between(sale_date, listing.get("listed_at") or listing.get("first_seen_at")),
                error, abs_error, abs_pct, within, prediction_source,
                sale.get("source") or "homes.co.nz", now_iso,
            ),
        )
        inserted += 1
    return inserted


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"n": 0}
    ratios = [r["sale_price"] / r["value_mid"] for r in rows if r.get("value_mid")]
    errors = [abs(r["sale_price"] - r["value_mid"]) for r in rows if r.get("value_mid")]
    pcts = [r["prediction_abs_pct"] for r in rows if r.get("prediction_abs_pct") is not None]
    within = [r["within_80_interval"] for r in rows if r.get("within_80_interval") is not None]
    return {
        "n": len(rows),
        "median_ratio": round(median(ratios), 6) if ratios else None,
        "mean_ratio": round(sum(ratios) / len(ratios), 6) if ratios else None,
        "median_abs_pct": round(median(pcts), 6) if pcts else None,
        "mae": round(sum(errors) / len(errors), 1) if errors else None,
        "coverage_80": round(sum(within) / len(within), 4) if within else None,
    }


def _calibration_for(rows: list[dict[str, Any]], scope: str, key: str) -> dict[str, Any]:
    summary = _summary(rows)
    return {"scope": scope, "scope_key": key, **summary}


def refresh_calibration(conn: sqlite3.Connection, *, now_iso: str) -> dict[str, Any]:
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute("SELECT * FROM listing_sale_outcomes")]
    conn.execute("DELETE FROM sale_feedback_calibration")
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(("global", "all"), []).append(row)
        if row.get("suburb_slug"):
            groups.setdefault(("suburb", str(row["suburb_slug"])), []).append(row)
        if row.get("property_type"):
            groups.setdefault(("property_type", str(row["property_type"])), []).append(row)
        if row.get("tenure"):
            groups.setdefault(("tenure", str(row["tenure"])), []).append(row)
    for (scope, key), group in groups.items():
        summary = _summary(group)
        if not summary.get("n"):
            continue
        conn.execute(
            """INSERT INTO sale_feedback_calibration (
                 scope, scope_key, n, median_ratio, mean_ratio, median_abs_pct,
                 mae, coverage_80, updated_at
               ) VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                scope, key, summary["n"], summary.get("median_ratio"),
                summary.get("mean_ratio"), summary.get("median_abs_pct"),
                summary.get("mae"), summary.get("coverage_80"), now_iso,
            ),
        )
    global_summary = _summary(groups.get(("global", "all"), []))
    return {"outcomes": len(rows), "calibration_groups": len(groups), **global_summary}


def _factor_for(conn: sqlite3.Connection, listing: dict[str, Any], global_row: dict[str, Any]) -> tuple[float, int, str]:
    """Choose a robust factor; require evidence before changing a displayed value."""
    candidates = [
        ("suburb", str(listing.get("suburb_slug") or "")),
        ("property_type", str(listing.get("property_type") or "")),
        ("tenure", str(listing.get("tenure") or "")),
    ]
    for scope, key in candidates:
        if not key:
            continue
        row = conn.execute(
            """SELECT n, median_ratio FROM sale_feedback_calibration
               WHERE scope=? AND scope_key=?""",
            (scope, key),
        ).fetchone()
        if row and row["n"] >= MIN_CALIBRATION_N and row["median_ratio"]:
            return round(float(row["median_ratio"]), 6), int(row["n"]), f"{scope}:{key}"
    if global_row.get("n", 0) >= MIN_CALIBRATION_N and global_row.get("median_ratio"):
        return round(float(global_row["median_ratio"]), 6), int(global_row["n"]), "global"
    return 1.0, int(global_row.get("n") or 0), "warming_up"


def _ml_predictions(conn: sqlite3.Connection, now_iso: str) -> dict[str, Any] | None:
    """Fit a ridge sale-price model only once enough realised outcomes exist."""
    frame = pd.read_sql_query(
        """SELECT o.sale_price, o.value_mid, o.asking_price, o.cv, o.bedrooms,
                  o.bathrooms, o.land_area, o.floor_area, o.build_year,
                  o.days_listing_to_sale, o.tenure, o.property_type,
                  o.suburb_slug, o.sale_method
           FROM listing_sale_outcomes o
           WHERE o.sale_price > 0 AND o.value_mid > 0""",
        conn,
    )
    if len(frame) < MIN_ML_N:
        return {"available": False, "n": len(frame), "reason": "warming_up"}
    frame = frame.copy()
    frame["value_log"] = np.log(frame["value_mid"].clip(lower=1))
    frame["asking_log"] = np.log(frame["asking_price"].where(frame["asking_price"] > 0))
    frame["cv_log"] = np.log(frame["cv"].where(frame["cv"] > 0))
    frame["land_log"] = np.log1p(frame["land_area"].clip(lower=0))
    frame["floor_log"] = np.log1p(frame["floor_area"].clip(lower=0))
    frame["build_year"] = pd.to_numeric(frame["build_year"], errors="coerce")
    frame["days_listing_to_sale"] = pd.to_numeric(frame["days_listing_to_sale"], errors="coerce")
    numeric = [
        "value_log", "asking_log", "cv_log", "land_log", "floor_log",
        "bedrooms", "bathrooms", "build_year", "days_listing_to_sale",
    ]
    categorical = ["tenure", "property_type", "suburb_slug", "sale_method"]
    y = np.log(frame["sale_price"].astype(float).clip(lower=1))
    pre = ColumnTransformer(
        [
            ("num", Pipeline([
                ("impute", SimpleImputer(strategy="median", add_indicator=True)),
                ("scale", StandardScaler()),
            ]), numeric),
            ("cat", Pipeline([
                ("impute", SimpleImputer(strategy="most_frequent")),
                ("onehot", OneHotEncoder(handle_unknown="ignore")),
            ]), categorical),
        ]
    )
    model = Pipeline([("pre", pre), ("ridge", Ridge(alpha=20.0, random_state=SEED))])
    n_splits = min(5, len(frame))
    oof = cross_val_predict(model, frame, y, cv=KFold(n_splits=n_splits, shuffle=True, random_state=SEED))
    mae = float(mean_absolute_error(np.exp(y), np.exp(oof)))
    mape = float(mean_absolute_percentage_error(np.exp(y), np.exp(oof)))
    model.fit(frame, y)

    active = pd.read_sql_query(
        """SELECT id, value_mid, asking_price, cv, bedrooms, bathrooms, land_area,
                  floor_area, build_year, days_on_market, tenure, property_type,
                  suburb_slug, sale_method
           FROM listings WHERE status='active' AND is_standard=1""",
        conn,
    )
    if active.empty:
        return {"available": True, "n": len(frame), "mae": round(mae, 1), "mape": round(mape, 4)}
    active = active.copy()
    active["value_log"] = np.log(active["value_mid"].clip(lower=1))
    active["asking_log"] = np.log(active["asking_price"].where(active["asking_price"] > 0))
    active["cv_log"] = np.log(active["cv"].where(active["cv"] > 0))
    active["land_log"] = np.log1p(active["land_area"].clip(lower=0))
    active["floor_log"] = np.log1p(active["floor_area"].clip(lower=0))
    active["build_year"] = pd.to_numeric(active["build_year"], errors="coerce")
    active["days_listing_to_sale"] = pd.to_numeric(active["days_on_market"], errors="coerce")
    preds = np.exp(model.predict(active))
    for listing_id, pred in zip(active["id"], preds):
        conn.execute(
            """INSERT INTO model_predictions
               (listing_id, model_name, low, mid, high, confidence, basis_json, created_at)
               VALUES (?,?,?,?,?,?,?,?)
               ON CONFLICT(listing_id, model_name) DO UPDATE SET
                 low=excluded.low, mid=excluded.mid, high=excluded.high,
                 confidence=excluded.confidence, basis_json=excluded.basis_json,
                 created_at=excluded.created_at""",
            (
                int(listing_id), "sale_feedback_ml", int(round(pred * 0.9)),
                int(round(pred)), int(round(pred * 1.1)), "medium",
                json.dumps({"model_version": MODEL_VERSION, "n": len(frame),
                            "mae": round(mae, 1), "mape": round(mape, 4)}),
                now_iso,
            ),
        )
    return {"available": True, "n": len(frame), "mae": round(mae, 1), "mape": round(mape, 4)}


def run(conn: sqlite3.Connection, *, now_iso: str | None = None) -> dict[str, Any]:
    now_iso = now_iso or _now()
    matched = match_outcomes(conn, now_iso=now_iso)
    calibration = refresh_calibration(conn, now_iso=now_iso)
    conn.row_factory = sqlite3.Row
    global_row = conn.execute(
        "SELECT * FROM sale_feedback_calibration WHERE scope='global' AND scope_key='all'"
    ).fetchone()
    global_dict = dict(global_row) if global_row else {}
    active = [
        dict(r) for r in conn.execute(
            """SELECT id, value_mid, value_low, value_high, suburb_slug, property_type, tenure
               FROM listings WHERE status='active' AND is_standard=1"""
        )
    ]
    applied = 0
    for listing in active:
        if not listing.get("value_mid"):
            continue
        factor, n, basis = _factor_for(conn, listing, global_dict)
        low = int(round((listing.get("value_low") or listing["value_mid"]) * factor))
        mid = int(round(listing["value_mid"] * factor))
        high = int(round((listing.get("value_high") or listing["value_mid"]) * factor))
        confidence = "medium" if basis != "warming_up" else "low"
        conn.execute(
            """INSERT INTO model_predictions
               (listing_id, model_name, low, mid, high, confidence, basis_json, created_at)
               VALUES (?,?,?,?,?,?,?,?)
               ON CONFLICT(listing_id, model_name) DO UPDATE SET
                 low=excluded.low, mid=excluded.mid, high=excluded.high,
                 confidence=excluded.confidence, basis_json=excluded.basis_json,
                 created_at=excluded.created_at""",
            (
                int(listing["id"]), "sale_feedback_v1", low, mid, high, confidence,
                json.dumps({"model_version": MODEL_VERSION, "n": n, "basis": basis,
                            "factor": factor, "status": "warming_up" if basis == "warming_up" else "calibrated"}),
                now_iso,
            ),
        )
        applied += 1
    ml = _ml_predictions(conn, now_iso)
    for key, value in (
        ("n_outcomes", calibration["outcomes"]),
        ("median_ratio", calibration.get("median_ratio")),
        ("median_abs_pct", calibration.get("median_abs_pct")),
        ("mae", calibration.get("mae")),
        ("coverage_80", calibration.get("coverage_80")),
        ("calibration_groups", calibration["calibration_groups"]),
        ("predictions_applied", applied),
    ):
        conn.execute(
            """INSERT INTO model_metrics (model_name, metric, value, detail_json, created_at)
               VALUES (?,?,?,?,?)
               ON CONFLICT(model_name, metric) DO UPDATE SET
                 value=excluded.value, detail_json=excluded.detail_json,
                 created_at=excluded.created_at""",
            (
                "sale_feedback", key, value,
                json.dumps({"model_version": MODEL_VERSION,
                            "ml": ml, "min_calibration_n": MIN_CALIBRATION_N}),
                now_iso,
            ),
        )
    if ml.get("available"):
        for key in ("n", "mae", "mape"):
            conn.execute(
                """INSERT INTO model_metrics (model_name, metric, value, detail_json, created_at)
                   VALUES (?,?,?,?,?)
                   ON CONFLICT(model_name, metric) DO UPDATE SET
                     value=excluded.value, detail_json=excluded.detail_json,
                     created_at=excluded.created_at""",
                ("sale_feedback_ml", key, ml.get(key),
                 json.dumps({"model_version": MODEL_VERSION}), now_iso),
            )
    return {
        "matched": matched,
        "outcomes": calibration["outcomes"],
        "median_ratio": calibration.get("median_ratio"),
        "mae": calibration.get("mae"),
        "predictions_applied": applied,
        "ml": ml,
    }


def main(argv: list[str] | None = None) -> int:
    import argparse
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Refresh sale-outcome feedback tables")
    parser.add_argument("--db", type=Path, default=root / "data" / "auckland_property.db")
    args = parser.parse_args(argv)
    conn = sqlite3.connect(args.db)
    try:
        print(json.dumps(run(conn, now_iso=_now()), indent=1))
        conn.commit()
    finally:
        conn.close()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
