"""Attach the Ministry school directory's Equity Index to cached schools.

Trade Me's school payload does not include a decile. The current Ministry school
directory publishes an Equity Index (EQi) but not the legacy decile, so this
module does not invent one. It stores EQi for context and leaves decile missing
where the source does not provide it.

Usage::

    python -m scraper.schools_enrich --download
    python -m scraper.schools_enrich --csv data/raw/schools_directory.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from . import config

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = config.DATA_DIR / "auckland_property.db"
DEFAULT_CSV = config.RAW_DIR / "schools_directory.csv"
DIRECTORY_URL = (
    "https://catalogue.data.govt.nz/dataset/c1923d33-e781-46c9-9ea1-d9b850082be4/"
    "resource/4b292323-9fcc-41f8-814b-3c7b19cf14b3/download/"
    "schooldirectory-28-10-2026-074531.csv"
)


def download(path: Path = DEFAULT_CSV) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(DIRECTORY_URL, timeout=60, headers={"User-Agent": "AucklandPropertyScout/1.0"})
    response.raise_for_status()
    path.write_bytes(response.content)
    return path


def load_rows(path: Path) -> dict[int, dict[str, Any]]:
    rows: dict[int, dict[str, Any]] = {}
    with path.open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                school_id = int(row.get("School_Id") or "")
            except (TypeError, ValueError):
                continue
            eqi = row.get("EQi_Index")
            try:
                eqi_value = int(float(eqi)) if eqi not in (None, "") else None
            except (TypeError, ValueError):
                eqi_value = None
            rows[school_id] = {
                "name": (row.get("Org_Name") or "").strip(),
                "eqi_index": eqi_value,
            }
    return rows


def run(db_path: Path = DEFAULT_DB, csv_path: Path = DEFAULT_CSV) -> dict[str, Any]:
    rows = load_rows(csv_path)
    conn = sqlite3.connect(db_path)
    updated = 0
    try:
        for school_id, source in rows.items():
            result = conn.execute(
                """UPDATE schools SET eqi_index=?, decile_source=COALESCE(decile_source, 'moe_directory')
                   WHERE id=?""",
                (source["eqi_index"], school_id),
            )
            updated += result.rowcount
        conn.commit()
    finally:
        conn.close()
    return {
        "directory_rows": len(rows),
        "schools_updated": updated,
        "source": str(csv_path),
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "note": "EQi is the current Ministry Equity Index; it is not a historical decile.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args(argv)
    if args.download or not args.csv.exists():
        download(args.csv)
    print(json.dumps(run(args.db, args.csv), indent=1))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
