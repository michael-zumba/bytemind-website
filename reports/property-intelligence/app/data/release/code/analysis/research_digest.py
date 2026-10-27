"""Regenerate the human-readable research digest from the current database.

The daily pipeline already rebuilds predictions, sale-method analysis and text
features. This module turns those tables into a dated brief so the written
"what the model currently says" commentary cannot drift behind the listings.

Usage::

    python -m analysis.research_digest --db data/auckland_property.db \
        --out research/latest-digest.md \
        --json data/exports/research-digest.json
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "auckland_property.db"
DEFAULT_MD = ROOT / "research" / "latest-digest.md"
DEFAULT_JSON = ROOT / "data" / "exports" / "research-digest.json"


def _json(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return value


def _meta(conn: sqlite3.Connection) -> dict[str, Any]:
    return {row["key"]: _json(row["value"]) for row in conn.execute("SELECT key, value FROM meta")}


def _scalar(conn: sqlite3.Connection, sql: str, args: Iterable[Any] = ()) -> Any:
    try:
        row = conn.execute(sql, tuple(args)).fetchone()
    except sqlite3.Error:
        return None
    return row[0] if row else None


def _metrics(conn: sqlite3.Connection) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for row in conn.execute(
        "SELECT model_name, metric, value, detail_json FROM model_metrics ORDER BY model_name, metric"
    ):
        detail = _json(row["detail_json"])
        out.setdefault(row["model_name"], {})[row["metric"]] = {
            "value": row["value"], "detail": detail,
        }
    return out


def _topics(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    try:
        rows = [dict(r) for r in conn.execute(
            """SELECT topic_id, label, top_terms, mean_weight, n_listings
               FROM text_topics ORDER BY topic_id"""
        )]
    except sqlite3.Error:
        return []
    for row in rows:
        terms = row.get("top_terms")
        try:
            row["top_terms"] = json.loads(terms) if isinstance(terms, str) else (terms or [])
        except json.JSONDecodeError:
            row["top_terms"] = [terms]
    return rows


def _events(conn: sqlite3.Connection) -> dict[str, Any]:
    try:
        counts = {r["event_type"]: r["n"] for r in conn.execute(
            "SELECT event_type, COUNT(*) AS n FROM listing_events GROUP BY event_type ORDER BY n DESC"
        )}
        recent = [dict(r) for r in conn.execute(
            """SELECT listing_id, event_type, event_at, old_value, new_value, detail_json
               FROM listing_events ORDER BY event_at DESC, id DESC LIMIT 12"""
        )]
    except sqlite3.Error:
        counts, recent = {}, []
    return {"counts": counts, "recent": recent}


def _sale_methods(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    try:
        return [dict(r) for r in conn.execute(
            """SELECT stage, label, n, median_avm_cv, median_ask_gap, median_dom,
                      ols_coef, ols_p, ols_n, ols_r2
               FROM sale_method_analysis ORDER BY stage"""
        )]
    except sqlite3.Error:
        return []


def _top_listings(conn: sqlite3.Connection) -> dict[str, list[dict[str, Any]]]:
    motivated: list[dict[str, Any]] = []
    value: list[dict[str, Any]] = []
    try:
        motivated = [dict(r) for r in conn.execute(
            """SELECT id, address, suburb_name, sale_pressure, sale_pressure_label,
                      sale_method_stage, asking_price, value_mid
               FROM listings WHERE is_standard=1 AND sale_pressure IS NOT NULL
               ORDER BY sale_pressure DESC, id LIMIT 5"""
        )]
    except sqlite3.Error:
        pass
    try:
        value = [dict(r) for r in conn.execute(
            """SELECT id, address, suburb_name, asking_price, value_mid,
                      ROUND((value_mid - asking_price) * 100.0 / value_mid, 1) AS gap_pct
               FROM listings
               WHERE is_standard=1 AND asking_price IS NOT NULL AND value_mid IS NOT NULL
                 AND value_confidence IN ('high','medium') AND tenure != 'leasehold'
               ORDER BY (value_mid - asking_price) * 1.0 / value_mid DESC, id LIMIT 5"""
        )]
    except sqlite3.Error:
        pass
    return {"most_motivated": motivated, "best_relative_value": value}


def _fmt_money(value: Any) -> str:
    if value is None:
        return "—"
    value = float(value)
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.2f}m"
    return f"${value / 1_000:.0f}k"


def _fmt_pct(value: Any) -> str:
    return "—" if value is None else f"{float(value) * 100:.2f}%"


def build_digest(conn: sqlite3.Connection, *, generated_at: str | None = None) -> dict[str, Any]:
    """Return a JSON-serialisable snapshot of everything the research UI shows."""
    meta = _meta(conn)
    counts = {
        "listings": _scalar(conn, "SELECT COUNT(*) FROM listings"),
        "active": _scalar(conn, "SELECT COUNT(*) FROM listings WHERE status='active'"),
        "delisted": _scalar(conn, "SELECT COUNT(*) FROM listings WHERE status='delisted'"),
        "standard": _scalar(conn, "SELECT COUNT(*) FROM listings WHERE is_standard=1"),
        "standard_active": _scalar(conn, "SELECT COUNT(*) FROM listings WHERE is_standard=1 AND status='active'"),
        "non_standard": _scalar(conn, "SELECT COUNT(*) FROM listings WHERE is_standard=0"),
        "sales": _scalar(conn, "SELECT COUNT(*) FROM sales"),
        "suburbs": _scalar(conn, "SELECT COUNT(*) FROM suburbs"),
    }
    coverage = {r["value_source"]: r["n"] for r in conn.execute(
        "SELECT value_source, COUNT(*) AS n FROM listings WHERE is_standard=1 GROUP BY value_source"
    )}
    metrics = _metrics(conn)
    text_meta = meta.get("text_analysis") if isinstance(meta.get("text_analysis"), dict) else {}
    sale_meta = meta.get("sale_method") if isinstance(meta.get("sale_method"), dict) else {}
    sale_methods = _sale_methods(conn)
    try:
        term_rows = [dict(r) for r in conn.execute(
            """SELECT term, term_group, dependent, n, n_with, effect_pct, q
               FROM text_term_associations WHERE dependent='value'
               ORDER BY q, term"""
        )]
    except sqlite3.Error:
        term_rows = []
    topics = _topics(conn)
    events = _events(conn)
    tops = _top_listings(conn)

    hedonic = metrics.get("hedonic_avm", {})
    no_cv = metrics.get("hedonic_no_cv", {})
    comp = metrics.get("comp_model", {})
    baseline = metrics.get("active_guide", {})
    sale_model = metrics.get("sale_cv", {})
    structural = metrics.get("hedonic_avm", {}).get("r2", {}).get("detail") or {}
    text_incremental = text_meta.get("incremental_model") or {}
    text_assoc = text_meta.get("associations") or {}
    fdr_counts = {}
    for dep, payload in text_assoc.items() if isinstance(text_assoc, dict) else []:
        if isinstance(payload, dict):
            fdr_counts[dep] = {
                "n": payload.get("n"),
                "significant_05": payload.get("n_significant_fdr_05"),
                "significant_10": payload.get("n_significant_fdr_10"),
                "min_q": min(
                    (f.get("q") for f in payload.get("features", []) if f.get("q") is not None),
                    default=None,
                ),
            }

    commentary = [
        f"Snapshot contains {counts['standard']} captured standard listings across {counts['suburbs']} "
        f"suburbs ({counts['standard_active']} active, {counts['delisted']} delisted; "
        f"{counts['listings']} collected in total).",
        "Valuation coverage: "
        + ", ".join(f"{k}={v}" for k, v in sorted(coverage.items())) + ".",
        f"Hedonic fallback (with CV): R² {structural.get('r2', '—')}, MAPE {_fmt_pct(structural.get('mape'))}; "
        f"no-CV variant MAPE {_fmt_pct(no_cv.get('mape', {}).get('value'))}.",
        f"Comparable-sales model vs Homes AVM: MAE {_fmt_money(comp.get('mae', {}).get('value'))}, "
        f"MAPE {_fmt_pct(comp.get('mape', {}).get('value'))}; old active-guide baseline MAPE "
        f"{_fmt_pct(baseline.get('mape', {}).get('value'))}.",
        f"Text layer: {text_meta.get('n_topics', len(topics))} topics; "
        f"incremental no-CV MAE delta {_fmt_money(text_incremental.get('delta', {}).get('mae_dollar'))}; "
        "individual topic/lexicon associations are reported with BH-FDR, not as proven price effects.",
        f"Sale-method ladder: {len(sale_methods)} stages, OLS R² {sale_meta.get('ols', {}).get('r2', '—')}; "
        "stage effects are cross-sectional and not treated as causal.",
        f"Observed changes: {sum(events['counts'].values())} events ("
        + ", ".join(f"{k}={v}" for k, v in events["counts"].items()) + ").",
    ]
    caveats = [
        "The model target is a Homes.co.nz AVM, not a sale price; it is a fallback/cross-check.",
        "Text signals are exploratory and conditional associations are FDR-controlled.",
        "Sale-method stages and pressure are motivation proxies, not causal price predictors.",
        "Predictions should be read with their interval and confidence label; this is research, not financial advice.",
    ]
    return {
        "generated_at": generated_at or datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "built_at": meta.get("built_at"),
        "model_version": meta.get("model_version"),
        "counts": counts,
        "coverage": coverage,
        "model": {
            "hedonic": hedonic,
            "no_cv": no_cv,
            "comp_model": comp,
            "active_guide": baseline,
            "sale_price": sale_model,
            "structural_detail": structural,
        },
        "text": {
            "model_version": text_meta.get("model_version"),
            "n_topics": text_meta.get("n_topics", len(topics)),
            "n_listings": text_meta.get("n_listings", _scalar(conn, "SELECT COUNT(*) FROM text_features")),
            "incremental_model": text_incremental,
            "fdr": fdr_counts,
            "topics": topics,
            "terms": term_rows,
            "term_summary": meta.get("text_terms"),
            "description_index": text_meta.get("description_index") or {},
        },
        "sale_method": {"meta": sale_meta, "stages": sale_methods},
        "events": events,
        "listings": tops,
        "commentary": commentary,
        "caveats": caveats,
    }


def _metric_row(block: dict[str, Any]) -> dict[str, Any]:
    detail = (block.get("r2") or {}).get("detail") or {}
    return {
        "r2": detail.get("r2"),
        "mae": detail.get("mae", (block.get("mae") or {}).get("value")),
        "mape": detail.get("mape", (block.get("mape") or {}).get("value")),
    }


def render_markdown(digest: dict[str, Any]) -> str:
    structural = digest["model"]["structural_detail"]
    lines = [
        "# Auckland Property Scout — research digest",
        "",
        f"Generated **{digest['generated_at']}** from database build **{digest['built_at'] or '—'}** "
        f"(`{digest['model_version'] or '—'}`). This file is regenerated after every build; "
        "do not edit it by hand.",
        "",
        "## Snapshot",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Captured standard listings | {digest['counts']['standard']} |",
        f"| Active standard listings | {digest['counts']['standard_active']} |",
        f"| Delisted standard listings retained | {digest['counts']['delisted']} |",
        f"| Collected listings (incl. non-standard) | {digest['counts']['listings']} |",
        f"| Non-standard listings | {digest['counts']['non_standard']} |",
        f"| Suburbs | {digest['counts']['suburbs']} |",
        f"| Nearby sold sales | {digest['counts']['sales']} |",
    ]
    for source, count in sorted(digest["coverage"].items()):
        lines.append(f"| Range source: {source} | {count} |")
    lines += ["", "## What the models currently say", ""]
    lines += ["| Signal | R² | MAE | MAPE |", "|---|---:|---:|---:|"]
    for label, raw_block in [
        ("Hedonic, with CV", digest["model"]["hedonic"]),
        ("Hedonic, no CV", digest["model"]["no_cv"]),
        ("Comparable sales", digest["model"]["comp_model"]),
        ("Active-guide baseline", digest["model"]["active_guide"]),
        ("Sold-price model", digest["model"]["sale_price"]),
    ]:
        block = _metric_row(raw_block)
        lines.append(
            f"| {label} | {block.get('r2') if block.get('r2') is not None else '—'} | {_fmt_money(block.get('mae'))} | "
            f"{_fmt_pct(block.get('mape'))} |"
        )
    lines += ["", "## Commentary", ""]
    lines += [f"- {item}" for item in digest["commentary"]]
    lines += ["", "## Description topics", ""]
    topics = digest["text"]["topics"]
    if topics:
        lines += ["| Topic | n | Mean weight | Top terms |", "|---|---:|---:|---|"]
        for topic in topics:
            terms = ", ".join(topic.get("top_terms") or [])
            lines.append(f"| {topic.get('label')} | {topic.get('n_listings')} | {topic.get('mean_weight')} | {terms} |")
    else:
        lines.append("_Text topics are not available in this database._")
    terms = [t for t in digest["text"].get("terms") or [] if t.get("q") is not None and t["q"] < 0.05]
    lines += ["", "## Critical description terms (value association, FDR < 5%)", ""]
    if terms:
        lines += ["| Term | Group | n with | Conditional effect | q |", "|---|---|---:|---:|---:|"]
        for term in terms:
            lines.append(
                f"| {term.get('term')} | {term.get('term_group')} | {term.get('n_with')} | "
                f"{term.get('effect_pct'):+.1f}% | {term.get('q'):.4g} |"
            )
        lines.append("")
        lines.append("Conditional on suburb, type, beds, baths, land/floor, DOM, tenure and sale method; "
                     "these are associations with the Homes AVM, not causal effects.")
    else:
        lines.append("_No curated term survives BH-FDR at 5% in this snapshot._")
    lines += ["", "## Sale-method ladder", ""]
    stages = digest["sale_method"]["stages"]
    if stages:
        lines += ["| Stage | n | Median AVM/CV | Median ask gap | Median DOM | OLS coef | p |", "|---|---:|---:|---:|---:|---:|---:|"]
        for stage in stages:
            lines.append(
                f"| {stage.get('label')} | {stage.get('n')} | {stage.get('median_avm_cv')} | "
                f"{stage.get('median_ask_gap')} | {stage.get('median_dom')} | {stage.get('ols_coef')} | {stage.get('ols_p')} |"
            )
    else:
        lines.append("_Sale-method analysis is not available yet._")
    lines += ["", "## Observed changes", ""]
    counts = digest["events"].get("counts") or {}
    lines.append(", ".join(f"{k}: {v}" for k, v in counts.items()) if counts else "No events recorded yet.")
    if digest["listings"]["most_motivated"]:
        lines += ["", "## Most motivated listings", "", "| Address | Suburb | Pressure | Stage | Asking |", "|---|---|---:|---:|---:|"]
        for item in digest["listings"]["most_motivated"]:
            lines.append(
                f"| {item.get('address')} | {item.get('suburb_name')} | {item.get('sale_pressure')} | "
                f"{item.get('sale_method_stage')} | {_fmt_money(item.get('asking_price'))} |"
            )
    lines += ["", "## Caveats", ""]
    lines += [f"- {item}" for item in digest["caveats"]]
    lines += ["", "---", "", "Regenerated by `analysis.research_digest`; see `research/model-evaluation.md` and `research/text-analysis.md` for methodology.", ""]
    return "\n".join(lines)


def write_digest(db_path: Path = DEFAULT_DB, md_path: Path = DEFAULT_MD, json_path: Path = DEFAULT_JSON) -> dict[str, Any]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        digest = build_digest(conn)
    finally:
        conn.close()
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(render_markdown(digest), encoding="utf-8")
    json_path.write_text(json.dumps(digest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return digest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--out", type=Path, default=DEFAULT_MD)
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON)
    args = parser.parse_args(argv)
    digest = write_digest(args.db, args.out, args.json)
    print(json.dumps({"markdown": str(args.out), "json": str(args.json),
                      "standard": digest["counts"]["standard"],
                      "generated_at": digest["generated_at"]}, indent=1))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
