"""Enrich listings with Homes.co.nz ownership, build-era and sale-history records.

Trade Me does not reliably publish tenure or build year. When a listing has a
Homes.co.nz property match, the public Homes property APIs expose:

* ``ownership`` (Freehold, Cross Lease, Leasehold, Unit Title, ...)
* ``decade_built`` and the property timeline's ``built`` event
* historical ``property_sale`` events with dates and prices

This module caches one JSON profile per Homes property under
``data/raw/homes/<property_id>.json`` and is safe to run daily: fresh profiles
are skipped according to ``--max-age-days``.

Usage::

    python -m scraper.homes_enrich                 # missing/stale profiles only
    python -m scraper.homes_enrich --limit 20      # small check
    python -m scraper.homes_enrich --max-age-days 30 --workers 4
"""
from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests

from . import config

DETAILS_URL = "https://api-gateway.homes.co.nz/details"
TIMELINE_URL = "https://gateway.homes.co.nz/property/{property_id}/timeline"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
)
DEFAULT_PROFILE_DIR = config.RAW_DIR / "homes"


def normalize_tenure(value: Any) -> str | None:
    text = str(value or "").strip().lower()
    if not text:
        return None
    if "cross" in text and "lease" in text:
        return "crosslease"
    if "leasehold" in text or "lease hold" in text:
        return "leasehold"
    if "unit title" in text or "stratum" in text:
        return "unit title"
    if "freehold" in text or "fee simple" in text:
        return "freehold"
    return text.replace(" ", "_")


def _year_from_date(value: Any) -> int | None:
    try:
        return int(str(value)[:4])
    except (TypeError, ValueError):
        return None


def _sales_from_timeline(timeline: dict[str, Any]) -> list[dict[str, Any]]:
    sales = []
    for event in timeline.get("events") or []:
        if event.get("key") != "property_sale":
            continue
        data = event.get("data") or {}
        price = data.get("price")
        try:
            price = int(price) if price is not None and str(price).strip() != "" else None
        except (TypeError, ValueError):
            price = None
        sales.append(
            {
                "sale_date": data.get("price_on") or event.get("date"),
                "sale_price": price,
                "display_price": data.get("display_price"),
                "sale_type": data.get("sale_type"),
                "council_confirmed": bool(data.get("council_confirmed")),
                "source": "homes.co.nz",
            }
        )
    sales.sort(key=lambda row: str(row.get("sale_date") or ""), reverse=True)
    return sales


def _build_year(timeline: dict[str, Any], details: dict[str, Any]) -> tuple[int | None, str | None]:
    for event in timeline.get("events") or []:
        if event.get("key") != "built":
            continue
        data = event.get("data") or {}
        year = _year_from_date(event.get("date")) or data.get("year_built")
        try:
            year = int(year) if year else None
        except (TypeError, ValueError):
            year = None
        if year:
            return year, "homes_timeline_approx"
    decade = details.get("decade_built")
    try:
        decade = int(decade) if decade else None
    except (TypeError, ValueError):
        decade = None
    return decade, "homes_decade" if decade else None


def profile_for(property_id: str, details: dict[str, Any], timeline: dict[str, Any]) -> dict[str, Any]:
    prop = details.get("property") or {}
    tenure = normalize_tenure(prop.get("ownership") or prop.get("ownership_type"))
    build_year, build_year_source = _build_year(timeline, prop)
    return {
        "property_id": property_id,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ownership_raw": prop.get("ownership") or prop.get("ownership_type"),
        "tenure": tenure,
        "tenure_source": "homes.co.nz" if tenure else None,
        "decade_built": prop.get("decade_built"),
        "build_year": build_year,
        "build_year_source": build_year_source,
        "land_use": prop.get("land_use"),
        "certificate_of_title": prop.get("certificate_of_title"),
        "sales": _sales_from_timeline(timeline),
        "details": details,
        "timeline": timeline,
    }


def _read_listing_property_ids(raw_dir: Path) -> dict[str, list[Path]]:
    out: dict[str, list[Path]] = {}
    for path in sorted((raw_dir / "listings").glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        homes = payload.get("homes") or {}
        property_id = homes.get("property_id")
        if property_id:
            out.setdefault(str(property_id), []).append(path)
    return out


def _fetch(property_id: str, timeout: int = 30) -> dict[str, Any]:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
    details_resp = session.get(DETAILS_URL, params={"property_id": property_id}, timeout=timeout)
    details_resp.raise_for_status()
    timeline: dict[str, Any] = {}
    try:
        timeline_resp = session.get(TIMELINE_URL.format(property_id=property_id), timeout=timeout)
        timeline_resp.raise_for_status()
        timeline = timeline_resp.json()
    except requests.RequestException:
        # A missing timeline should not discard ownership and build-era data.
        timeline = {}
    return profile_for(property_id, details_resp.json(), timeline)


def _fresh(path: Path, max_age_days: float) -> bool:
    if not path.exists() or max_age_days <= 0:
        return False
    age = datetime.now(timezone.utc).timestamp() - path.stat().st_mtime
    return age < max_age_days * 86400


def run(
    raw_dir: Path = config.RAW_DIR,
    out_dir: Path = DEFAULT_PROFILE_DIR,
    *,
    max_age_days: float = 30,
    workers: int = 4,
    delay: float = 0.2,
    limit: int | None = None,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    property_ids = _read_listing_property_ids(raw_dir)
    todo = [
        property_id for property_id in property_ids
        if not _fresh(out_dir / f"{property_id}.json", max_age_days)
    ]
    if limit is not None:
        todo = todo[: max(0, limit)]
    fetched = 0
    failed = 0
    skipped = len(property_ids) - len(todo)

    def task(property_id: str) -> tuple[str, bool, str | None]:
        try:
            if delay:
                time.sleep(delay)
            profile = _fetch(property_id)
            target = out_dir / f"{property_id}.json"
            temp = target.with_suffix(".json.tmp")
            temp.write_text(json.dumps(profile, ensure_ascii=False, indent=1), encoding="utf-8")
            temp.replace(target)
            return property_id, True, None
        except Exception as exc:  # noqa: BLE001 - one bad profile must not stop the batch
            return property_id, False, str(exc)[:200]

    with ThreadPoolExecutor(max_workers=max(1, min(workers, 8))) as pool:
        futures = {pool.submit(task, property_id): property_id for property_id in todo}
        for future in as_completed(futures):
            property_id, ok, error = future.result()
            if ok:
                fetched += 1
            else:
                failed += 1
                print(f"WARN homes {property_id}: {error}")
    return {
        "properties_with_homes": len(property_ids),
        "skipped_fresh": skipped,
        "fetched": fetched,
        "failed": failed,
        "profile_dir": str(out_dir),
        "max_age_days": max_age_days,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=config.RAW_DIR)
    parser.add_argument("--out", type=Path, default=DEFAULT_PROFILE_DIR)
    parser.add_argument("--max-age-days", type=float, default=30)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--delay", type=float, default=0.2)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args(argv)
    result = run(
        args.raw_dir, args.out,
        max_age_days=args.max_age_days, workers=args.workers,
        delay=args.delay, limit=args.limit,
    )
    print(json.dumps(result, indent=1))
    return 0 if not result["failed"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
