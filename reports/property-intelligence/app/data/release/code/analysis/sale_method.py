"""Sale-method stage, sale-pressure proxy and descriptive tests.

Trade Me listings move through a rough motivation ladder:

    auction -> tender/deadline -> negotiation -> price guide (enquiries over)
    -> asking price

The ordering is a hypothesis about vendor/agent expectation and urgency, not a causal
law. This module encodes the stage, builds a bounded pressure score from stage, days
on market and observed price/method changes, and tests whether stages differ in
AVM-to-CV premium once suburb, type and size are controlled for.
"""
from __future__ import annotations

import json
import math
import sqlite3
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MODEL_VERSION = "sale-stage-v1"

STAGE_LABELS = {
    0: "Auction",
    1: "Tender",
    2: "Deadline sale",
    3: "Price by negotiation",
    4: "Price guide / enquiries over",
    5: "Asking price",
    9: "Other",
}


def stage_for(sale_method: str | None, asking_kind: str | None = None) -> int:
    method = (sale_method or "").lower().strip()
    kind = (asking_kind or "").lower().strip()
    if method == "auction":
        return 0
    if method == "tender":
        return 1
    if method == "deadline":
        return 2
    if method == "negotiation":
        return 3
    if method == "asking":
        return 4 if kind in {"enquiries_over", "price_guide"} else 5
    if method == "other":
        return 9
    return 9


def pressure_score(stage: int, days_on_market: int | None, price_drops: int = 0, method_changes: int = 0) -> float:
    """0-100 heuristic. Higher means more observable motivation to transact.

    The components are deliberately simple and bounded so the score cannot be
    dominated by a single stale or unusual listing.
    """
    stage_component = (min(max(stage, 0), 5) / 5.0) * 50.0
    dom_component = min(max(days_on_market or 0, 0), 180) / 180.0 * 30.0
    event_component = min(20.0, price_drops * 8.0 + method_changes * 10.0)
    return round(stage_component + dom_component + event_component, 1)


def pressure_label(score: float) -> str:
    if score >= 65:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def _median(values: list[float]) -> float | None:
    clean = [v for v in values if v is not None and not (isinstance(v, float) and math.isnan(v))]
    return round(statistics.median(clean), 4) if clean else None


def run(conn: sqlite3.Connection, *, now_iso: str | None = None) -> dict[str, Any]:
    now_iso = now_iso or datetime.now(timezone.utc).isoformat()
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute(
        """SELECT id, sale_method, asking_kind, days_on_market, value_mid, estimate_mid,
                  cv, cv_ratio, ask_gap, suburb_name, property_type, bedrooms,
                  bathrooms, land_area, floor_area, is_standard
           FROM listings"""
    )]

    events: dict[int, dict[str, int]] = {}
    try:
        for event in conn.execute(
            """SELECT listing_id, event_type, detail_json FROM listing_events
               WHERE event_at >= datetime('now', '-180 days')"""
        ):
            bucket = events.setdefault(event["listing_id"], {"drops": 0, "method": 0})
            if event["event_type"] == "price_change":
                try:
                    detail = json.loads(event["detail_json"] or "{}")
                except json.JSONDecodeError:
                    detail = {}
                if detail.get("direction") == "drop":
                    bucket["drops"] += 1
            elif event["event_type"] == "method_change":
                bucket["method"] += 1
    except sqlite3.Error:
        events = {}

    for row in rows:
        stage = stage_for(row["sale_method"], row["asking_kind"])
        counts = events.get(row["id"], {"drops": 0, "method": 0})
        score = pressure_score(stage, row["days_on_market"], counts["drops"], counts["method"])
        conn.execute(
            """UPDATE listings SET sale_method_stage=?, sale_pressure=?, sale_pressure_label=?
               WHERE id=?""",
            (stage, score, pressure_label(score), row["id"]),
        )

    standard = [
        r for r in rows
        if (r["is_standard"] or 0) == 1 and stage_for(r["sale_method"], r["asking_kind"]) != 9
    ]
    for row in standard:
        row["stage"] = stage_for(row["sale_method"], row["asking_kind"])
        row["avm_cv"] = (
            row["estimate_mid"] / row["cv"]
            if row["estimate_mid"] and row["cv"] else None
        )
        row["value_cv"] = (
            row["value_mid"] / row["cv"]
            if row["value_mid"] and row["cv"] else None
        )

    ols = _stage_ols(standard)
    for stage, label in STAGE_LABELS.items():
        group = [r for r in standard if r["stage"] == stage]
        if not group:
            continue
        coef = ols.get(stage, {})
        conn.execute(
            """INSERT INTO sale_method_analysis
               (stage, label, n, median_value_ratio, median_ask_gap, median_dom,
                median_avm_cv, ols_coef, ols_p, ols_n, ols_r2, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(stage) DO UPDATE SET
                 label=excluded.label, n=excluded.n,
                 median_value_ratio=excluded.median_value_ratio,
                 median_ask_gap=excluded.median_ask_gap, median_dom=excluded.median_dom,
                 median_avm_cv=excluded.median_avm_cv, ols_coef=excluded.ols_coef,
                 ols_p=excluded.ols_p, ols_n=excluded.ols_n, ols_r2=excluded.ols_r2,
                 updated_at=excluded.updated_at""",
            (
                stage, label, len(group),
                _median([r["value_cv"] for r in group if r["value_cv"] is not None]),
                _median([r["ask_gap"] for r in group if r["ask_gap"] is not None]),
                _median([r["days_on_market"] for r in group if r["days_on_market"] is not None]),
                _median([r["avm_cv"] for r in group if r["avm_cv"] is not None]),
                coef.get("coef"), coef.get("p"), ols.get("n"), ols.get("r2"), now_iso,
            ),
        )
    conn.commit()
    return {
        "model_version": MODEL_VERSION,
        "stages": {str(k): v for k, v in STAGE_LABELS.items()},
        "n": len(standard),
        "ols": ols,
        "updated_at": now_iso,
    }


def _stage_ols(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Test stage differences in AVM/CV, controlling for location, type and size."""
    data = [
        r for r in rows
        if r.get("estimate_mid") and r.get("cv") and r.get("stage") in STAGE_LABELS
        and (r.get("stage") if r.get("stage") is not None else 9) != 9
    ]
    if len(data) < 60:
        return {"n": len(data), "r2": None, "note": "too few observations"}
    try:
        import numpy as np
        import pandas as pd
        import statsmodels.formula.api as smf
    except ImportError as exc:  # pragma: no cover
        return {"n": len(data), "r2": None, "note": f"statsmodels unavailable: {exc}"}

    frame = pd.DataFrame(data)
    frame["log_ratio"] = np.log(frame["estimate_mid"] / frame["cv"])
    frame["log_land"] = np.log1p(frame["land_area"].fillna(0))
    frame["log_floor"] = np.log1p(frame["floor_area"].fillna(0))
    frame["stage_c"] = pd.Categorical(frame["stage"], categories=list(STAGE_LABELS.keys()))
    formula = (
        "log_ratio ~ C(stage_c) + C(suburb_name) + C(property_type) "
        "+ bedrooms + bathrooms + log_land + log_floor"
    )
    try:
        model = smf.ols(formula, data=frame).fit(cov_type="HC3")
    except Exception as exc:  # noqa: BLE001
        return {"n": len(data), "r2": None, "note": f"OLS failed: {exc}"}

    out: dict[str, Any] = {"n": int(model.nobs), "r2": round(float(model.rsquared), 4), "terms": {}}
    for term in model.params.index:
        if not term.startswith("C(stage_c)"):
            continue
        stage = int(term.split("[T.")[1].rstrip("]"))
        out[stage] = {
            "coef": round(float(model.params[term]), 4),
            "p": round(float(model.pvalues[term]), 4),
        }
        out["terms"][term] = out[stage]
    return out


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Compute sale-method stages and pressure")
    parser.add_argument("--db", default=str(Path(__file__).resolve().parent.parent / "data" / "auckland_property.db"))
    args = parser.parse_args()
    conn = sqlite3.connect(args.db)
    try:
        result = run(conn)
        print(json.dumps(result, indent=1))
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
