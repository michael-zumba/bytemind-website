"""Term-level associations between listing language and property value.

The NMF topic model is deliberately coarse (12 topics). This module tests a
small, pre-specified vocabulary of interpretable property phrases so a user can
see *which* language travels with a higher or lower value rather than only a
blended topic score.

Two dependent variables are tested separately:

* ``value``   — ``log(value_mid)``: conditional association with the value range
* ``premium`` — ``log(value_mid / cv)``: relative to the council CV

Controls are the same structural/design matrix used by the text model:
suburb, property type, beds, baths, land/floor area, days on market, tenure and
sale method. OLS uses HC3 robust standard errors and Benjamini-Hochberg FDR
across the pre-specified terms within each dependent variable. These are
conditional associations, not causal effects; the term set is fixed before the
regressions, so it is not a data-mined top-N list.

Usage::

    python -m analysis.text_terms --db data/auckland_property.db
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests

from analysis import text_model

MODEL_VERSION = "text-terms-v1"
MIN_LISTINGS = 50

# (group, human phrase). Keep this list fixed before looking at coefficients.
TERMS: list[tuple[str, str]] = [
    ("views", "waterfront"), ("views", "sea view"), ("views", "sea"),
    ("views", "harbour"), ("views", "ocean"), ("views", "beach"),
    ("views", "coastal"), ("views", "rangitoto"), ("views", "skyline"),
    ("views", "reserve"), ("views", "park"),
    ("quality", "brand new"), ("quality", "new build"), ("quality", "modern"),
    ("quality", "renovat"), ("quality", "do up"), ("quality", "original"),
    ("quality", "character"), ("quality", "villa"), ("quality", "brick"),
    ("quality", "plaster"),
    ("school", "school"), ("school", "westlake"), ("school", "school zone"),
    ("school", "in zone"),
    ("land", "section"), ("land", "land"), ("land", "subdivision"),
    ("land", "development"), ("land", "zoning"), ("land", "freehold"),
    ("land", "leasehold"), ("land", "cross lease"),
    ("amenity", "pool"), ("amenity", "tennis"), ("amenity", "garden"),
    ("amenity", "deck"), ("amenity", "garage"), ("amenity", "parking"),
    ("investment", "investment"), ("investment", "rental"),
    ("investment", "tenanted"), ("investment", "home and income"),
    ("investment", "granny"), ("investment", "income"),
    ("location", "walking distance"), ("location", "transport"),
    ("location", "motorway"), ("location", "village"),
    ("orientation", "north facing"), ("orientation", "sunny"),
    ("orientation", "quiet"), ("orientation", "private"),
    ("risk", "as is"), ("risk", "leaky"), ("risk", "earthquake"),
]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS text_term_associations (
    term TEXT NOT NULL,
    term_group TEXT NOT NULL,
    dependent TEXT NOT NULL,
    n INTEGER,
    n_with INTEGER,
    coef REAL,
    se REAL,
    p REAL,
    q REAL,
    effect_pct REAL,
    mean_value_with REAL,
    mean_value_without REAL,
    mean_premium_with REAL,
    mean_premium_without REAL,
    model_version TEXT,
    updated_at TEXT,
    PRIMARY KEY (term, dependent)
);
"""


def _phrase(term: str) -> re.Pattern[str]:
    words = [re.escape(word) for word in term.split()]
    return re.compile(r"(?<!\w)" + r"\s+".join(words) + r"(?!\w)")


def _bh(pvalues: Sequence[float]) -> np.ndarray:
    out = np.full(len(pvalues), np.nan, dtype=float)
    mask = ~np.isnan(np.asarray(pvalues, dtype=float))
    if mask.any():
        out[mask] = multipletests(np.asarray(pvalues, dtype=float)[mask], method="fdr_bh")[1]
    return out


def _fit_term(
    y: pd.Series,
    presence: np.ndarray,
    structural: pd.DataFrame,
) -> tuple[float, float, float, int] | None:
    mask = y.notna().to_numpy()
    if mask.sum() < 40 or presence[mask].sum() < 5:
        return None
    design = pd.concat(
        [
            structural.loc[mask],
            pd.Series(presence[mask].astype(float), index=structural.index[mask], name="term"),
        ],
        axis=1,
    )
    design = sm.add_constant(design, has_constant="add")
    try:
        fit = sm.OLS(y.astype(float)[mask], design).fit(cov_type="HC3")
        return (
            float(fit.params["term"]),
            float(fit.bse["term"]),
            float(fit.pvalues["term"]),
            int(mask.sum()),
        )
    except (ValueError, KeyError, np.linalg.LinAlgError):
        return None


def run(conn: sqlite3.Connection, *, model_version: str = MODEL_VERSION) -> dict[str, Any]:
    """Fit term associations and replace ``text_term_associations``."""
    frame = text_model.load_listings(conn)
    if len(frame) < MIN_LISTINGS:
        raise ValueError(f"Need at least {MIN_LISTINGS} descriptions, found {len(frame)}")
    texts, cleaning = text_model.clean_corpus(frame["body"].tolist())
    structural = text_model.build_structural_design(frame)
    value = pd.to_numeric(frame["value_mid"], errors="coerce")
    cv = pd.to_numeric(frame["cv"], errors="coerce")
    y_value = np.log(value.where(value > 0))
    y_premium = np.log((value / cv).where((value > 0) & (cv > 0)))
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(_SCHEMA)
    conn.execute("DELETE FROM text_term_associations")

    rows: list[dict[str, Any]] = []
    for dependent, target in (("value", y_value), ("premium", y_premium)):
        candidates: list[dict[str, Any]] = []
        for group, term in TERMS:
            presence = np.array([bool(_phrase(term).search(text)) for text in texts])
            fit = _fit_term(target, presence, structural)
            if fit is None:
                continue
            coef, se, p, n = fit
            if not all(np.isfinite(value) for value in (coef, se, p)):
                continue
            effect = np.exp(coef) - 1.0
            if not np.isfinite(effect):
                effect = None
            mask = target.notna().to_numpy()
            with_mask = mask & presence
            without_mask = mask & ~presence
            candidates.append({
                "term": term,
                "term_group": group,
                "dependent": dependent,
                "n": n,
                "n_with": int(presence.sum()),
                "coef": coef,
                "se": se,
                "p": p,
                "effect_pct": round(float(effect) * 100.0, 2) if effect is not None else None,
                "mean_value_with": round(float(value[with_mask].mean()), 0) if with_mask.any() else None,
                "mean_value_without": round(float(value[without_mask].mean()), 0) if without_mask.any() else None,
                "mean_premium_with": round(float((value[with_mask] / cv[with_mask]).mean()), 4) if with_mask.any() else None,
                "mean_premium_without": round(float((value[without_mask] / cv[without_mask]).mean()), 4) if without_mask.any() else None,
            })
        qvals = _bh([row["p"] for row in candidates])
        for row, q in zip(candidates, qvals):
            row["q"] = round(float(q), 6) if not np.isnan(q) else None
            row["model_version"] = model_version
            row["updated_at"] = now
            rows.append(row)

    conn.executemany(
        """INSERT OR REPLACE INTO text_term_associations
           (term, term_group, dependent, n, n_with, coef, se, p, q, effect_pct,
            mean_value_with, mean_value_without, mean_premium_with, mean_premium_without,
            model_version, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        [
            (
                row["term"], row["term_group"], row["dependent"], row["n"], row["n_with"],
                row["coef"], row["se"], row["p"], row["q"], row["effect_pct"],
                row["mean_value_with"], row["mean_value_without"],
                row["mean_premium_with"], row["mean_premium_without"],
                row["model_version"], row["updated_at"],
            )
            for row in rows
        ],
    )
    conn.commit()

    def sig(dep: str, alpha: float = 0.05) -> list[dict[str, Any]]:
        return [
            {
                "term": r["term"], "group": r["term_group"], "effect_pct": r["effect_pct"],
                "q": r["q"], "n_with": r["n_with"],
            }
            for r in sorted(rows, key=lambda item: item["q"] or 1.0)
            if r["dependent"] == dep and r["q"] is not None and r["q"] < alpha
        ]

    return {
        "model_version": model_version,
        "n_listings": int(len(frame)),
        "n_terms": len(TERMS),
        "n_associations": len(rows),
        "cleaning": cleaning,
        "value_significant_fdr_05": sig("value"),
        "premium_significant_fdr_05": sig("premium"),
        "top_value": sorted(
            [r for r in rows if r["dependent"] == "value"], key=lambda item: item["q"] or 1.0
        )[:12],
        "top_premium": sorted(
            [r for r in rows if r["dependent"] == "premium"], key=lambda item: item["q"] or 1.0
        )[:12],
        "note": (
            "Curated pre-specified phrases; OLS controls for suburb, type, beds, baths, "
            "land/floor area, DOM, tenure and sale method; HC3 + BH-FDR within each dependent. "
            "Associations are conditional, not causal, and the value target is the Homes AVM."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "auckland_property.db")
    args = parser.parse_args(argv)
    conn = sqlite3.connect(args.db)
    try:
        summary = run(conn)
    finally:
        conn.close()
    print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
