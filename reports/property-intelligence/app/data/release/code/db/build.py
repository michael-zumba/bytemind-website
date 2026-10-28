"""Build the SQLite database from data/raw/listings/*.json.

Usage::

    python -m db.build
    python -m db.build --raw-dir data/raw --db data/auckland_property.db

The build is atomic: it writes a temporary database, computes valuations/statistics,
then swaps it into place. Existing snapshot history and first-seen timestamps are
preserved across rebuilds.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from analysis import comps, sale_method

try:  # optional ML layers; fail gracefully during early rebuilds
    from analysis import text_model
except ImportError:
    text_model = None
try:
    from analysis import text_terms
except ImportError:
    text_terms = None
try:
    from analysis import valuation_model
except ImportError:
    valuation_model = None

from scraper import config
from scraper.parse import days_on_market

DB_PATH = config.DATA_DIR / "auckland_property.db"
RAW_DIR = config.RAW_DIR
EXPORT_DIR = config.DATA_DIR / "exports"

CSV_COLUMNS = [
    "id", "title", "address", "suburb", "property_type", "bedrooms", "bathrooms",
    "parking", "land_area", "floor_area", "price_display", "asking_price",
    "sale_method", "deadline_at", "listed_at", "days_on_market",
    "estimate_low", "estimate_mid", "estimate_high", "estimate_updated_at",
    "comp_low", "comp_mid", "comp_high", "comp_confidence",
    "value_low", "value_mid", "value_high", "value_source", "value_confidence",
    "cv", "land_value", "improvement_value", "cv_ratio", "ask_gap", "deal_gap",
    "lat", "lon", "url", "agency_name", "agency_phone", "homes_url", "tenure",
    "tenure_source", "build_decade", "build_year",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_listing_files(raw_dir: Path) -> list[dict[str, Any]]:
    # Current cache files are .json; old/delisted files are archived as .json.gz.
    # Prefer an uncompressed file if both exist, and de-duplicate by listing id.
    files = sorted((raw_dir / "listings").glob("*.json")) + sorted(
        (raw_dir / "listings").glob("*.json.gz")
    )
    listings: dict[int, dict[str, Any]] = {}
    for path in files:
        try:
            if path.name.endswith(".json.gz"):
                with gzip.open(path, "rt", encoding="utf-8") as fh:
                    data = json.load(fh)
            else:
                with path.open(encoding="utf-8") as fh:
                    data = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and data.get("listing_id"):
            listings.setdefault(int(data["listing_id"]), data)
    return list(listings.values())


def load_homes_profiles(raw_dir: Path) -> dict[str, dict[str, Any]]:
    """Load cached Homes.co.nz ownership/build/sale profiles by property ID."""
    profiles: dict[str, dict[str, Any]] = {}
    for path in sorted((raw_dir / "homes").glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        property_id = payload.get("property_id")
        if property_id:
            profiles[str(property_id)] = payload
    return profiles


def previous_state(
    db_path: Path,
) -> tuple[dict[int, str], list[dict[str, Any]], dict[int, dict[str, Any]], list[dict[str, Any]]]:
    if not db_path.exists():
        return {}, [], {}, []
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        first_seen = {
            int(row["id"]): row["first_seen_at"]
            for row in conn.execute("SELECT id, first_seen_at FROM listings")
            if row["first_seen_at"]
        }
        snapshots = [dict(row) for row in conn.execute("SELECT * FROM listing_snapshots")]
        previous: dict[int, dict[str, Any]] = {}
        listing_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(listings)")
        }
        delisted_expr = "delisted_at" if "delisted_at" in listing_columns else "NULL AS delisted_at"
        for row in conn.execute(
            f"""SELECT id, address, price_display, asking_price, sale_method, asking_kind,
                       estimate_mid, cv, value_mid, status, last_seen_at, body, {delisted_expr}
                FROM listings"""
        ):
            previous[int(row["id"])] = dict(row)
        try:
            events = [dict(row) for row in conn.execute("SELECT * FROM listing_events")]
        except sqlite3.Error:
            events = []
        conn.close()
        return first_seen, snapshots, previous, events
    except sqlite3.Error:
        return {}, [], {}, []


def canonical_suburb(name: str | None) -> str | None:
    if not name:
        return None
    key = name.strip().lower()
    for suburb in config.SUBURBS:
        if key in {suburb["name"].lower(), suburb["tm_name"].lower(), suburb["slug"]}:
            return suburb["name"]
    # Trade Me nearby sales use upper-case suburb names.
    return name.strip().title()


def address_key(address: str | None) -> str | None:
    if not address:
        return None
    cleaned = " ".join(address.lower().replace(",", " ").split())
    return "addr:" + hashlib.sha1(cleaned.encode("utf-8")).hexdigest()[:16]


def _int(value: Any) -> int | None:
    try:
        return int(value) if value is not None and value != "" else None
    except (TypeError, ValueError):
        return None


def _float(value: Any) -> float | None:
    try:
        return float(value) if value is not None and value != "" else None
    except (TypeError, ValueError):
        return None


NON_STANDARD_KEYWORDS = (
    "relocatable home", "relocatable house", "transportable home",
    "tiny home", "tiny house", "house truck", "caravan", "motorhome",
    "floating home", "houseboat", "container home", "for removal",
    "house removal", "removal house", "house to be removed",
)


def _infer_build_year(item: dict[str, Any]) -> int | None:
    """Fallback for build year explicitly stated in the listing copy."""
    import re

    text = f"{item.get('title') or ''} {item.get('body') or ''}"
    match = re.search(
        r"\b(?:built|constructed|construction|year built|built in)\b[^.]{0,28}?\b((?:18|19|20)\d{2})\b",
        text,
        re.IGNORECASE,
    )
    if not match:
        return None
    try:
        year = int(match.group(1))
    except ValueError:
        return None
    return year if 1800 <= year <= datetime.now().year + 1 else None


def classify_listing(item: dict[str, Any]) -> tuple[int, str | None, str]:
    """Flag non-standard listings and detect tenure.

    Trade Me lists relocatable/tiny homes in the residential category. Leasehold
    apartments are standard property but their asking price cannot be compared
    directly with a freehold AVM, so tenure is stored separately.
    """
    title = (item.get("title") or "").lower()
    body_full = (item.get("body") or "").lower()
    body = body_full[:1800]
    property_type = (item.get("property_type") or "").lower()
    text = f"{title} {body}"
    tenure_text = f"{title} {body_full}"

    tenure = "unknown"
    if "leasehold" in tenure_text:
        tenure = "leasehold"
    elif "crosslease" in tenure_text or "cross-lease" in tenure_text or "cross lease" in tenure_text:
        tenure = "crosslease"
    elif "unit title" in tenure_text:
        tenure = "unit title"
    elif "fee simple" in tenure_text or "freehold" in tenure_text:
        tenure = "freehold"

    if property_type in {"house", "unit", "townhouse", "apartment", ""}:
        for keyword in NON_STANDARD_KEYWORDS:
            if keyword in text:
                return 0, f"non-standard dwelling: {keyword}", tenure
    if "per week" in (item.get("price_display") or "").lower():
        return 0, "looks like a rental listing", tenure
    return 1, None, tenure


def insert_listings(
    conn: sqlite3.Connection,
    listings: list[dict[str, Any]],
    first_seen: dict[int, str],
    profiles: dict[str, dict[str, Any]] | None = None,
) -> int:
    suburb_slugs = {s["slug"] for s in config.SUBURBS}
    profiles = profiles or {}
    count = 0
    for item in listings:
        listing_id = int(item["listing_id"])
        slug = item.get("suburb_slug")
        if slug not in suburb_slugs:
            # Fall back to a name lookup, then skip listings outside the target set.
            for s in config.SUBURBS:
                if (item.get("suburb") or "").lower() in {s["name"].lower(), s["tm_name"].lower()}:
                    slug = s["slug"]
                    break
        if slug not in suburb_slugs:
            continue
        captured = item.get("captured_at") or utc_now()
        seen_before = first_seen.get(listing_id) or captured
        homes = item.get("homes") or {}
        detail = item.get("detail") or {}
        dom = days_on_market(item.get("listed_at"), captured)
        is_standard, standard_reason, tenure = classify_listing(item)
        conn.execute(
            """INSERT OR REPLACE INTO listings (
                 id, title, address, suburb_slug, suburb_name, district, region,
                 property_type, bedrooms, bathrooms, lounges, parking, land_area,
                 floor_area, price_display, asking_price, asking_kind, sale_method,
                 deadline_at, listed_at, end_at, as_at, lat, lon, canonical_path, url,
                 photo_url, photos_json, body, agent_name, agency_name, agency_phone,
                 agency_website, member_nickname, member_id, view_count, watchers,
                 detail_ok, detail_error, estimate_low, estimate_mid, estimate_high,
                 estimate_source, estimate_updated_at, estimate_matched,
                 homes_property_id, homes_url, cv, land_value, improvement_value,
                 cv_updated_at, build_decade, cv_ratio, ask_gap, deal_gap,
                 days_on_market, first_seen_at, last_seen_at, status, is_standard,
                 standard_reason, tenure
               ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                listing_id, item.get("title"), item.get("address"), slug,
                item.get("suburb") or next((s["name"] for s in config.SUBURBS if s["slug"] == slug), None),
                item.get("district"), item.get("region"), item.get("property_type"),
                _int(item.get("bedrooms")), _int(item.get("bathrooms")), _int(item.get("lounges")),
                _int(item.get("parking")), _float(item.get("land_area")), _float(item.get("floor_area")),
                item.get("price_display"), _int(item.get("asking_price")), item.get("asking_kind"),
                item.get("sale_method"), item.get("deadline_at"), item.get("listed_at"),
                item.get("end_at"), item.get("as_at"), _float(item.get("lat")), _float(item.get("lon")),
                item.get("canonical_path"), item.get("url"), item.get("photo_url"),
                json.dumps(item.get("photos") or [], ensure_ascii=False), item.get("body"),
                None,
                item.get("agency_name"), item.get("agency_phone"), item.get("agency_website"),
                item.get("member_nickname"), _int(item.get("member_id")),
                _int(item.get("view_count")), _int(item.get("watchers")),
                1 if item.get("detail_ok") else 0, item.get("detail_error"),
                _int(homes.get("estimate_low")), _int(homes.get("estimate_mid")),
                _int(homes.get("estimate_high")), "homes_avm" if homes.get("estimate_mid") else None,
                homes.get("estimate_updated_at"), 1 if homes.get("estimate_mid") else 0,
                homes.get("property_id"), homes.get("homes_url"),
                _int(homes.get("cv")), _int(homes.get("land_value")),
                _int(homes.get("improvement_value")), homes.get("cv_updated_at"),
                homes.get("build_decade"), None, None, None, dom, seen_before, captured, "active",
                is_standard, standard_reason, tenure,
            ),
        )
        profile = profiles.get(str(homes.get("property_id") or ""))
        profile_tenure = (profile or {}).get("tenure")
        profile_source = (profile or {}).get("tenure_source")
        if profile:
            conn.execute(
                """UPDATE listings SET
                     tenure=COALESCE(?, tenure),
                     tenure_source=?,
                     build_decade=COALESCE(?, build_decade),
                     build_year=?,
                     build_year_source=?
                   WHERE id=?""",
                (
                    profile_tenure,
                    profile_source or "homes.co.nz",
                    profile.get("decade_built"),
                    _int(profile.get("build_year")),
                    profile.get("build_year_source"),
                    listing_id,
                ),
            )
        else:
            text_year = _infer_build_year(item)
            conn.execute(
                """UPDATE listings SET tenure_source=?,
                     build_year=COALESCE(build_year, ?),
                     build_year_source=COALESCE(build_year_source, ?)
                   WHERE id=?""",
                (
                    "listing_text" if tenure != "unknown" else "unknown",
                    text_year,
                    "listing_text_approx" if text_year else None,
                    listing_id,
                ),
            )
        conn.execute(
            """INSERT OR IGNORE INTO listing_snapshots (
                 listing_id, captured_at, price_display, asking_price, estimate_mid, cv,
                 view_count, watchers, days_on_market, value_mid, sale_method
               ) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                listing_id, captured, item.get("price_display"), _int(item.get("asking_price")),
                _int(homes.get("estimate_mid")), _int(homes.get("cv")),
                _int(item.get("view_count")), _int(item.get("watchers")), dom, None,
                item.get("sale_method"),
            ),
        )
        for row in homes.get("history") or []:
            if not row.get("date"):
                continue
            conn.execute(
                """INSERT OR REPLACE INTO estimate_history
                   (listing_id, date, estimate_low, estimate_mid, estimate_high)
                   VALUES (?,?,?,?,?)""",
                (listing_id, row["date"], _int(row.get("estimate_low")),
                 _int(row.get("estimate_mid")), _int(row.get("estimate_high"))),
            )
        for row in homes.get("suburb_history") or []:
            if not row.get("date") or not row.get("estimate_mid"):
                continue
            conn.execute(
                """INSERT OR REPLACE INTO suburb_estimate_history
                   (suburb_slug, date, estimate_mid) VALUES (?,?,?)""",
                (slug, row["date"], _int(row["estimate_mid"])),
            )
        for school in item.get("schools") or []:
            if not school.get("school_id"):
                continue
            conn.execute(
                """INSERT OR REPLACE INTO schools
                   (id, name, type, authority, roll, gender, decile, address, suburb, lat, lon)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    _int(school["school_id"]), school.get("name"), school.get("type"),
                    school.get("authority"), _int(school.get("roll")), school.get("gender"),
                    _int(school.get("decile")), school.get("address"), school.get("suburb"),
                    _float(school.get("lat")), _float(school.get("lon")),
                ),
            )
            conn.execute(
                """INSERT OR REPLACE INTO listing_schools (listing_id, school_id, in_zone)
                   VALUES (?,?,?)""",
                (listing_id, _int(school["school_id"]), 1 if school.get("in_zone") else 0),
            )
        count += 1
    return count


def insert_sales(conn: sqlite3.Connection, listings: list[dict[str, Any]]) -> int:
    count = 0
    property_cache: set[str] = set()
    for item in listings:
        source_suburb = canonical_suburb(item.get("suburb"))
        for comp in item.get("comps") or []:
            price = _int(comp.get("sale_price"))
            if not price:
                continue
            suburb = canonical_suburb(comp.get("suburb")) or source_suburb
            property_id = comp.get("property_id") or address_key(comp.get("address"))
            if not property_id:
                continue
            conn.execute(
                """INSERT OR IGNORE INTO sales (
                     property_id, address, suburb, sale_price, sale_date, lat, lon,
                     land_area, floor_area, bedrooms, bathrooms, property_type, cv,
                     land_value, improvement_value, estimate_low, estimate_mid, estimate_high,
                     distance_km, source, source_detail
                   ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    property_id, comp.get("address"), suburb, price, comp.get("sale_date"),
                    _float(comp.get("lat")), _float(comp.get("lon")), _float(comp.get("land_area")),
                    _float(comp.get("floor_area")), _int(comp.get("bedrooms")),
                    _int(comp.get("bathrooms")), comp.get("property_type"), _int(comp.get("cv")),
                    _int(comp.get("land_value")), _int(comp.get("improvement_value")),
                    _int(comp.get("estimate_low")), _int(comp.get("estimate_mid")),
                    _int(comp.get("estimate_high")), _float(comp.get("distance_km")),
                    comp.get("source") or "trademe_nearby_sales",
                    json.dumps({"source_listing_id": item.get("listing_id")}, ensure_ascii=False),
                ),
            )
            if conn.total_changes:
                count += 1
            if property_id not in property_cache:
                conn.execute(
                    """INSERT INTO properties (
                         id, homes_property_id, address, suburb, lat, lon, cv, land_value,
                         improvement_value, land_area, floor_area, bedrooms, bathrooms,
                         property_type, build_decade, cv_updated_at, last_sale_price, last_sale_date
                       ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                       ON CONFLICT(id) DO UPDATE SET
                         cv=COALESCE(excluded.cv, properties.cv),
                         land_value=COALESCE(excluded.land_value, properties.land_value),
                         improvement_value=COALESCE(excluded.improvement_value, properties.improvement_value),
                         land_area=COALESCE(excluded.land_area, properties.land_area),
                         floor_area=COALESCE(excluded.floor_area, properties.floor_area),
                         bedrooms=COALESCE(excluded.bedrooms, properties.bedrooms),
                         bathrooms=COALESCE(excluded.bathrooms, properties.bathrooms),
                         property_type=COALESCE(excluded.property_type, properties.property_type),
                         cv_updated_at=COALESCE(excluded.cv_updated_at, properties.cv_updated_at),
                         last_sale_price=excluded.last_sale_price,
                         last_sale_date=excluded.last_sale_date""",
                    (
                        property_id, comp.get("property_id"), comp.get("address"), suburb,
                        _float(comp.get("lat")), _float(comp.get("lon")), _int(comp.get("cv")),
                        _int(comp.get("land_value")), _int(comp.get("improvement_value")),
                        _float(comp.get("land_area")), _float(comp.get("floor_area")),
                        _int(comp.get("bedrooms")), _int(comp.get("bathrooms")),
                        comp.get("property_type"), None, comp.get("cv_updated_at"),
                        price, comp.get("sale_date"),
                    ),
                )
                property_cache.add(property_id)
    return count


def upsert_listing_properties(conn: sqlite3.Connection, listings: list[dict[str, Any]]) -> None:
    for item in listings:
        homes = item.get("homes") or {}
        property_id = homes.get("property_id")
        if not property_id:
            continue
        conn.execute(
            """INSERT INTO properties (
                 id, homes_property_id, address, suburb, lat, lon, cv, land_value,
                 improvement_value, land_area, floor_area, bedrooms, bathrooms,
                 property_type, build_decade, cv_updated_at
               ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(id) DO UPDATE SET
                 cv=COALESCE(excluded.cv, properties.cv),
                 land_value=COALESCE(excluded.land_value, properties.land_value),
                 improvement_value=COALESCE(excluded.improvement_value, properties.improvement_value),
                 land_area=COALESCE(excluded.land_area, properties.land_area),
                 floor_area=COALESCE(excluded.floor_area, properties.floor_area),
                 property_type=COALESCE(excluded.property_type, properties.property_type),
                 build_decade=COALESCE(excluded.build_decade, properties.build_decade),
                 cv_updated_at=COALESCE(excluded.cv_updated_at, properties.cv_updated_at)""",
            (
                property_id, property_id,
                f"{item.get('address')}, {item.get('suburb')}".strip(", "),
                item.get("suburb"), _float(item.get("lat")), _float(item.get("lon")),
                _int(homes.get("cv")), _int(homes.get("land_value")),
                _int(homes.get("improvement_value")), _float(item.get("land_area")),
                _float(item.get("floor_area")), _int(item.get("bedrooms")),
                _int(item.get("bathrooms")), item.get("property_type"),
                homes.get("build_decade"), homes.get("cv_updated_at"),
            ),
        )


def insert_property_sales(
    conn: sqlite3.Connection,
    listings: list[dict[str, Any]],
    profiles: dict[str, dict[str, Any]],
    now_iso: str,
) -> int:
    """Materialise subject-property sale histories from cached Homes profiles."""
    conn.execute("DELETE FROM property_sales")
    inserted = 0
    for item in listings:
        homes = item.get("homes") or {}
        property_id = str(homes.get("property_id") or "")
        profile = profiles.get(property_id)
        if not profile:
            continue
        listing_id = _int(item.get("listing_id"))
        address = f"{item.get('address') or ''}, {item.get('suburb') or ''}".strip(", ")
        for sale in profile.get("sales") or []:
            conn.execute(
                """INSERT INTO property_sales (
                     homes_property_id, listing_id, address, sale_date, sale_price,
                     display_price, sale_type, council_confirmed, source, updated_at
                   ) VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    property_id, listing_id, address, sale.get("sale_date"),
                    _int(sale.get("sale_price")), sale.get("display_price"),
                    sale.get("sale_type"), 1 if sale.get("council_confirmed") else 0,
                    sale.get("source") or "homes.co.nz", now_iso,
                ),
            )
            inserted += 1
    return inserted


def _current_inventory_ids(raw_dir: Path) -> set[int] | None:
    """IDs from the latest complete 17-suburb search cache, or None if incomplete."""
    search_files = sorted((raw_dir / "search").glob("*.json"))
    if len(search_files) < len(config.SUBURBS):
        return None
    ids: set[int] = set()
    for path in search_files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if payload.get("total_count") is None:
            return None
        for item in payload.get("items") or []:
            try:
                ids.add(int(item["ListingId"]))
            except (KeyError, TypeError, ValueError):
                return None
    return ids or None


def reconcile_inventory(
    conn: sqlite3.Connection,
    raw_dir: Path,
    previous: dict[int, dict[str, Any]],
    now_iso: str,
) -> dict[str, Any]:
    """Mark listings absent from the latest complete search as delisted.

    One row per listing is retained: the description body, snapshots, predictions and
    text features are not copied into a separate archive table. Reappearing listings are
    marked active again and both transitions are written to ``listing_events``.
    """
    current_ids = _current_inventory_ids(raw_dir)
    if current_ids is None:
        return {"available": False, "marked_delisted": 0, "relisted": 0}
    conn.execute("CREATE TEMP TABLE IF NOT EXISTS _current_inventory (id INTEGER PRIMARY KEY)")
    conn.execute("DELETE FROM _current_inventory")
    conn.executemany(
        "INSERT OR IGNORE INTO _current_inventory(id) VALUES (?)",
        [(listing_id,) for listing_id in current_ids],
    )
    # A listing that reappears in search is active again. In the normal build path
    # insert_listings() already resets it; this also handles direct reconciliations.
    conn.execute(
        """UPDATE listings SET status='active', delisted_at=NULL
           WHERE status='delisted' AND id IN (SELECT id FROM _current_inventory)"""
    )
    delisted_rows = [
        dict(r) for r in conn.execute(
            """SELECT id, address FROM listings
               WHERE status='active' AND id NOT IN (SELECT id FROM _current_inventory)"""
        )
    ]
    for row in delisted_rows:
        old = previous.get(int(row["id"]), {})
        was_delisted = old.get("status") == "delisted"
        delisted_at = old.get("delisted_at") or now_iso
        conn.execute(
            "UPDATE listings SET status='delisted', delisted_at=? WHERE id=?",
            (delisted_at, row["id"]),
        )
        if not was_delisted:
            conn.execute(
                """INSERT OR IGNORE INTO listing_events
                   (listing_id, event_type, event_at, old_value, new_value, detail_json)
                   VALUES (?,?,?,?,?,?)""",
                (row["id"], "delisted", now_iso, "active", "delisted",
                 json.dumps({"address": row.get("address")}, ensure_ascii=False)),
            )
    relisted = 0
    for listing_id, old in previous.items():
        if old.get("status") == "delisted" and listing_id in current_ids:
            conn.execute(
                """INSERT OR IGNORE INTO listing_events
                   (listing_id, event_type, event_at, old_value, new_value, detail_json)
                   VALUES (?,?,?,?,?,?)""",
                (listing_id, "relisted", now_iso, "delisted", "active", "{}"),
            )
            relisted += 1
    conn.execute("DROP TABLE _current_inventory")
    return {
        "available": True,
        "inventory_ids": len(current_ids),
        "marked_delisted": len(delisted_rows),
        "relisted": relisted,
    }


def _body_digest(body: Any) -> str | None:
    """Whitespace-insensitive hash for detecting editorial description changes."""
    if not body:
        return None
    text = " ".join(str(body).split()).strip()
    if not text:
        return None
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def generate_events(
    conn: sqlite3.Connection,
    previous_listings: dict[int, dict[str, Any]],
    old_events: list[dict[str, Any]],
    *,
    had_previous: bool,
    now_iso: str,
) -> int:
    """Preserve old events and derive new price/method/AVM change events.

    Events are keyed by listing + event type + time + values, so rebuilding the
    same raw snapshot twice is idempotent. First build does not emit 1,000
    "new listing" events; later builds do.
    """
    inserted = 0
    for event in old_events:
        conn.execute(
            """INSERT OR IGNORE INTO listing_events
               (listing_id, event_type, event_at, old_value, new_value, detail_json)
               VALUES (?,?,?,?,?,?)""",
            (
                event.get("listing_id"), event.get("event_type"), event.get("event_at"),
                event.get("old_value") or "", event.get("new_value") or "",
                event.get("detail_json"),
            ),
        )
    current_rows = [
        dict(row) for row in conn.execute(
            """SELECT id, address, price_display, asking_price, sale_method, asking_kind,
                      estimate_mid, cv, value_mid, first_seen_at, last_seen_at, status, body
               FROM listings"""
        )
    ]
    current_ids = {int(r["id"]) for r in current_rows}

    def add(listing_id: int, event_type: str, event_at: str | None,
            old_value: Any, new_value: Any, detail: dict[str, Any]) -> None:
        nonlocal inserted
        old_s = "" if old_value is None else str(old_value)
        new_s = "" if new_value is None else str(new_value)
        cur = conn.execute(
            """INSERT OR IGNORE INTO listing_events
               (listing_id, event_type, event_at, old_value, new_value, detail_json)
               VALUES (?,?,?,?,?,?)""",
            (listing_id, event_type, event_at or now_iso, old_s, new_s,
             json.dumps(detail, ensure_ascii=False)),
        )
        if cur.rowcount:
            inserted += 1

    for row in current_rows:
        listing_id = int(row["id"])
        prev = previous_listings.get(listing_id)
        if prev is None:
            if had_previous:
                add(listing_id, "new_listing", row.get("first_seen_at"),
                    "", row.get("address") or "", {"price_display": row.get("price_display")})
            continue
        old_price, new_price = prev.get("asking_price"), row.get("asking_price")
        if old_price != new_price:
            if old_price is None and new_price is not None:
                direction = "set"
            elif old_price is not None and new_price is None:
                direction = "removed"
            elif (new_price or 0) < (old_price or 0):
                direction = "drop"
            else:
                direction = "increase"
            add(
                listing_id, "price_change", row.get("last_seen_at"), old_price, new_price,
                {
                    "direction": direction,
                    "old_display": prev.get("price_display"),
                    "new_display": row.get("price_display"),
                },
            )
        elif prev.get("price_display") != row.get("price_display"):
            add(
                listing_id, "price_display_change", row.get("last_seen_at"),
                prev.get("price_display"), row.get("price_display"),
                {"old_price": old_price, "new_price": new_price},
            )
        old_method = (prev.get("sale_method"), prev.get("asking_kind"))
        new_method = (row.get("sale_method"), row.get("asking_kind"))
        if old_method != new_method:
            add(
                listing_id, "method_change", row.get("last_seen_at"),
                "/".join(str(x or "") for x in old_method),
                "/".join(str(x or "") for x in new_method),
                {"old": old_method, "new": new_method},
            )
        old_est, new_est = prev.get("estimate_mid"), row.get("estimate_mid")
        if old_est and new_est and abs(new_est - old_est) / old_est >= 0.005:
            add(listing_id, "estimate_change", row.get("last_seen_at"), old_est, new_est,
                {"pct": round((new_est - old_est) / old_est, 4)})
        old_cv, new_cv = prev.get("cv"), row.get("cv")
        if old_cv != new_cv:
            add(listing_id, "cv_change", row.get("last_seen_at"), old_cv, new_cv, {})
        # Description edits are a sentiment signal: an agent may rewrite the copy
        # before changing the price. Compare a whitespace-normalised digest so a
        # reformat alone is not treated as a change.
        old_body = prev.get("body")
        new_body = row.get("body")
        old_digest = _body_digest(old_body)
        new_digest = _body_digest(new_body)
        if old_digest and new_digest and old_digest != new_digest:
            add(
                listing_id, "description_change", row.get("last_seen_at"),
                old_digest, new_digest,
                {
                    "old_chars": len(str(old_body or "")),
                    "new_chars": len(str(new_body or "")),
                },
            )
    # Removals cannot be inferred from the raw cache (files are retained); the next
    # iteration can add a search-membership flag if required.
    return inserted


def restore_snapshots(conn: sqlite3.Connection, snapshots: list[dict[str, Any]]) -> None:
    for snap in snapshots:
        conn.execute(
            """INSERT OR IGNORE INTO listing_snapshots (
                 listing_id, captured_at, price_display, asking_price, estimate_mid, cv,
                 view_count, watchers, days_on_market, value_mid, sale_method
               ) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                snap.get("listing_id"), snap.get("captured_at"), snap.get("price_display"),
                snap.get("asking_price"), snap.get("estimate_mid"), snap.get("cv"),
                snap.get("view_count"), snap.get("watchers"), snap.get("days_on_market"),
                snap.get("value_mid"), snap.get("sale_method"),
            ),
        )


def _iso_moment(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value)).astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def _days_between(later: Any, earlier: Any) -> float | None:
    a, b = _iso_moment(later), _iso_moment(earlier)
    if a is None or b is None:
        return None
    return round((a - b).total_seconds() / 86400, 2)


def build_price_history(conn: sqlite3.Connection, *, now_iso: str) -> dict[str, int]:
    """Materialise dated asking-price observations and change-speed indicators.

    Sources are (a) retained listing snapshots, (b) the append-only
    ``listing_events`` price-change ledger, and (c) the current listing when it
    has never had a snapshot. One row is written per distinct observed state,
    not per daily scrape. Auction/POA observations are retained with a NULL
    price so a later price set can be dated.
    """
    conn.execute("DELETE FROM listing_price_history")
    conn.execute("DELETE FROM listing_price_dynamics")

    listings = {
        int(row["id"]): dict(row)
        for row in conn.execute(
            """SELECT id, asking_price, price_display, sale_method, first_seen_at,
                      last_seen_at, status FROM listings"""
        )
    }
    snapshots: dict[int, list[dict[str, Any]]] = {}
    for row in conn.execute(
        """SELECT listing_id, captured_at, asking_price, price_display, sale_method
           FROM listing_snapshots ORDER BY listing_id, captured_at"""
    ):
        snapshots.setdefault(int(row["listing_id"]), []).append(dict(row))
    events: dict[int, list[dict[str, Any]]] = {}
    for row in conn.execute(
        """SELECT listing_id, event_type, event_at, old_value, new_value, detail_json
           FROM listing_events
           WHERE event_type IN ('price_change', 'delisted', 'relisted')
           ORDER BY listing_id, event_at, id"""
    ):
        events.setdefault(int(row["listing_id"]), []).append(dict(row))

    def point(
        when: Any, price: Any, display: Any, method: Any, event_type: str, source: str,
        *, previous_price: int | None = None, change_amount: int | None = None,
        change_pct: float | None = None, days_since_previous: float | None = None,
    ) -> dict[str, Any]:
        value = _int(price)
        return {
            "observed_at": str(when), "price": value,
            "price_display": display, "sale_method": method,
            "event_type": event_type, "source": source,
            "previous_price": previous_price,
            "change_amount": change_amount, "change_pct": change_pct,
            "days_since_previous": days_since_previous,
        }

    inserted = 0
    for listing_id, listing in listings.items():
        raw_points: list[dict[str, Any]] = []
        event_times = {
            _iso_moment(event.get("event_at"))
            for event in events.get(listing_id, [])
            if event.get("event_type") == "price_change"
        }
        event_times.discard(None)
        for snap in snapshots.get(listing_id, []):
            # An event row already describes the old and new states at its
            # timestamp; keeping the same-time snapshot would duplicate the
            # change and can even make it look like the price moved back.
            if _iso_moment(snap.get("captured_at")) in event_times:
                continue
            raw_points.append(point(
                snap.get("captured_at"), snap.get("asking_price"), snap.get("price_display"),
                snap.get("sale_method"), "observation", "snapshot",
            ))
        # Reconstruct the pre-change state when the snapshot window was compacted
        # before the first retained capture. Event timestamps are the only date we
        # can honestly attach to these values.
        for event in events.get(listing_id, []):
            if event.get("event_type") != "price_change":
                continue
            detail: dict[str, Any] = {}
            if event.get("detail_json"):
                try:
                    parsed = json.loads(event["detail_json"])
                    if isinstance(parsed, dict):
                        detail = parsed
                except (TypeError, ValueError):
                    pass
            old_price = _int(event.get("old_value"))
            new_price = _int(event.get("new_value"))
            if old_price is not None:
                raw_points.append(point(
                    event.get("event_at"), old_price, detail.get("old_display"),
                    None, "price_before_change", "event",
                ))
            raw_points.append(point(
                event.get("event_at"), new_price, detail.get("new_display"),
                None, "price_change", "event",
            ))
        # If the current listing has no captured point at all, use the current
        # state as the first observation rather than inventing history.
        if not raw_points:
            raw_points.append(point(
                listing.get("last_seen_at") or listing.get("first_seen_at"),
                listing.get("asking_price"), listing.get("price_display"),
                listing.get("sale_method"), "first_observed", "listing",
            ))
        raw_points = [p for p in raw_points if _iso_moment(p["observed_at"]) is not None]
        raw_points.sort(key=lambda p: (_iso_moment(p["observed_at"]) or datetime.min.replace(tzinfo=timezone.utc), p["event_type"]))

        previous_observed: str | None = None
        previous_price: int | None = None
        seen_any = False
        for raw in raw_points:
            # Only asking-price changes create history rows. Display/method edits
            # are already captured in listing_events and would otherwise produce a
            # noisy row every time a snapshot and an event describe the same state.
            if seen_any and raw["price"] == previous_price:
                continue
            if not seen_any:
                event_type = "first_observed"
                change_amount = change_pct = days_since = None
            else:
                days_since = _days_between(raw["observed_at"], previous_observed)
                change_amount = (
                    raw["price"] - previous_price
                    if raw["price"] is not None and previous_price is not None
                    else None
                )
                change_pct = (
                    round(change_amount / previous_price, 6)
                    if change_amount is not None and previous_price
                    else None
                )
                if previous_price is None and raw["price"] is not None:
                    event_type = "price_set"
                elif previous_price is not None and raw["price"] is None:
                    event_type = "price_removed"
                else:
                    event_type = "price_change"
            conn.execute(
                """INSERT INTO listing_price_history (
                     listing_id, observed_at, price, price_display, sale_method,
                     event_type, previous_price, change_amount, change_pct,
                     days_since_previous, source
                   ) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    listing_id, raw["observed_at"], raw["price"], raw["price_display"],
                    raw["sale_method"], event_type, previous_price, change_amount,
                    change_pct, days_since, raw["source"],
                ),
            )
            inserted += 1
            previous_observed = raw["observed_at"]
            previous_price = raw["price"]
            seen_any = True

    # Materialised speed/sentiment indicators. These are descriptive of what was
    # observed; they do not claim a causal price trajectory.
    dynamics = 0
    histories: dict[int, list[dict[str, Any]]] = {}
    for row in conn.execute(
        """SELECT * FROM listing_price_history ORDER BY listing_id, observed_at, id"""
    ):
        histories.setdefault(int(row["listing_id"]), []).append(dict(row))
    description_events: dict[int, list[dict[str, Any]]] = {}
    for row in conn.execute(
        """SELECT listing_id, event_at FROM listing_events
           WHERE event_type='description_change' ORDER BY listing_id, event_at"""
    ):
        description_events.setdefault(int(row["listing_id"]), []).append(dict(row))

    for listing_id, listing in listings.items():
        history = histories.get(listing_id, [])
        priced = [row for row in history if row["price"] is not None]
        changes = [
            row for row in history
            if row["event_type"] in {"price_change", "price_set", "price_removed"}
        ]
        first_price = priced[0]["price"] if priced else None
        current_price = priced[-1]["price"] if priced else None
        first_change = changes[0] if changes else None
        last_change = changes[-1] if changes else None
        desc = description_events.get(listing_id, [])
        first_seen = listing.get("first_seen_at")
        intervals = [
            _days_between(changes[index]["observed_at"], changes[index - 1]["observed_at"])
            for index in range(1, len(changes))
        ]
        intervals = [value for value in intervals if value is not None]
        cumulative = (
            current_price - first_price
            if current_price is not None and first_price is not None
            else None
        )
        cumulative_pct = (
            round(cumulative / first_price, 6)
            if cumulative is not None and first_price
            else None
        )
        drops = [
            row["change_amount"] for row in changes
            if row.get("change_amount") is not None and row["change_amount"] < 0
        ]
        drop_pcts = [
            row["change_pct"] for row in changes
            if row.get("change_pct") is not None and row["change_pct"] < 0
        ]
        if last_change:
            if last_change["event_type"] == "price_removed":
                direction = "removed"
            elif last_change["change_amount"] is None:
                direction = "set"
            elif last_change["change_amount"] < 0:
                direction = "drop"
            else:
                direction = "increase"
        else:
            direction = None
        conn.execute(
            """INSERT INTO listing_price_dynamics (
                 listing_id, first_price, current_price, n_observations,
                 n_price_changes, n_description_changes, first_change_at,
                 last_change_at, first_description_change_at,
                 last_description_change_at, days_to_first_change,
                 days_since_last_change, avg_days_between_changes,
                 cumulative_change, cumulative_change_pct, largest_drop,
                 largest_drop_pct, last_direction, updated_at
               ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                listing_id, first_price, current_price, len(history), len(changes),
                len(desc), first_change["observed_at"] if first_change else None,
                last_change["observed_at"] if last_change else None,
                desc[0]["event_at"] if desc else None,
                desc[-1]["event_at"] if desc else None,
                _days_between(first_change["observed_at"], first_seen)
                if first_change and first_seen else None,
                _days_between(now_iso, last_change["observed_at"])
                if last_change else None,
                round(sum(intervals) / len(intervals), 2) if intervals else None,
                cumulative, cumulative_pct,
                min(drops) if drops else None,
                min(drop_pcts) if drop_pcts else None,
                direction, now_iso,
            ),
        )
        dynamics += 1
    return {"price_observations": inserted, "price_dynamics": dynamics}


def update_suburb_centroids(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        """SELECT suburb_slug, AVG(lat) AS lat, AVG(lon) AS lon, COUNT(*) AS n
           FROM listings WHERE lat IS NOT NULL AND lon IS NOT NULL GROUP BY suburb_slug"""
    ).fetchall()
    for row in rows:
        conn.execute(
            "UPDATE suburbs SET lat=?, lon=? WHERE slug=?",
            (row["lat"], row["lon"], row["suburb_slug"]),
        )


def compact_history(conn: sqlite3.Connection, *, now_iso: str) -> dict[str, Any]:
    """Bound snapshot growth while keeping the research panel usable.

    Within the recent window every capture is kept. Older snapshots are reduced to
    the first and last capture per listing per calendar month; the event ledger
    still records every observed price/method change. This keeps daily monitoring
    detailed now and month-level history later without duplicating descriptions.
    """
    from datetime import datetime, timedelta, timezone

    cutoff = datetime.fromisoformat(now_iso).astimezone(timezone.utc) - timedelta(days=120)
    estimate_cutoff = cutoff - timedelta(days=245)
    rows = [dict(r) for r in conn.execute(
        "SELECT id, listing_id, captured_at FROM listing_snapshots ORDER BY listing_id, captured_at"
    )]
    keep: set[int] = set()
    latest_by_listing: dict[int, tuple[str, int]] = {}
    month_first: dict[tuple[int, str], tuple[str, int]] = {}
    month_last: dict[tuple[int, str], tuple[str, int]] = {}
    for row in rows:
        try:
            moment = datetime.fromisoformat(row["captured_at"]).astimezone(timezone.utc)
        except (TypeError, ValueError):
            keep.add(int(row["id"]))
            continue
        latest = latest_by_listing.get(int(row["listing_id"]))
        if latest is None or moment >= latest[0]:
            latest_by_listing[int(row["listing_id"])] = (moment, int(row["id"]))
        if moment >= cutoff:
            keep.add(int(row["id"]))
            continue
        month = moment.strftime("%Y-%m")
        key = (int(row["listing_id"]), month)
        if key not in month_first or moment < month_first[key][0]:
            month_first[key] = (moment, int(row["id"]))
        if key not in month_last or moment > month_last[key][0]:
            month_last[key] = (moment, int(row["id"]))
    keep.update(rid for _, rid in latest_by_listing.values())
    keep.update(rid for _, rid in month_first.values())
    keep.update(rid for _, rid in month_last.values())
    remove = [int(row["id"]) for row in rows if int(row["id"]) not in keep]
    for start in range(0, len(remove), 500):
        chunk = remove[start:start + 500]
        conn.execute(
            f"DELETE FROM listing_snapshots WHERE id IN ({','.join('?' for _ in chunk)})", chunk
        )

    # Est AVM history is only used for trend/backtests; keep daily for a year, then monthly.
    est_rows = [dict(r) for r in conn.execute(
        "SELECT rowid AS rid, listing_id, date FROM estimate_history ORDER BY listing_id, date"
    )]
    est_keep: set[int] = set()
    est_latest: dict[int, tuple[str, int]] = {}
    est_months: dict[tuple[int, str], tuple[str, int]] = {}
    for row in est_rows:
        try:
            moment = datetime.fromisoformat(str(row["date"])).astimezone(timezone.utc)
        except (TypeError, ValueError):
            est_keep.add(int(row["rid"]))
            continue
        latest = est_latest.get(int(row["listing_id"]))
        if latest is None or moment >= latest[0]:
            est_latest[int(row["listing_id"])] = (moment, int(row["rid"]))
        if moment >= estimate_cutoff:
            est_keep.add(int(row["rid"]))
            continue
        key = (int(row["listing_id"]), moment.strftime("%Y-%m"))
        if key not in est_months or moment < est_months[key][0]:
            est_months[key] = (moment, int(row["rid"]))
    est_keep.update(rid for _, rid in est_latest.values())
    est_keep.update(rid for _, rid in est_months.values())
    est_remove = [int(row["rid"]) for row in est_rows if int(row["rid"]) not in est_keep]
    for start in range(0, len(est_remove), 500):
        chunk = est_remove[start:start + 500]
        conn.execute(
            f"DELETE FROM estimate_history WHERE rowid IN ({','.join('?' for _ in chunk)})", chunk
        )
    return {
        "snapshots_before": len(rows),
        "snapshots_keep": len(rows) - len(remove),
        "snapshots_removed": len(remove),
        "estimate_history_before": len(est_rows),
        "estimate_history_keep": len(est_rows) - len(est_remove),
        "estimate_history_removed": len(est_remove),
        "snapshot_days_full": 120,
        "older_snapshot_rule": "first+last capture per listing per month",
    }


def write_meta(conn: sqlite3.Connection, metadata: dict[str, Any]) -> None:
    for key, value in metadata.items():
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
            (key, json.dumps(value) if not isinstance(value, str) else value),
        )


def export_csv(conn: sqlite3.Connection, path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = conn.execute(
        f"""SELECT {', '.join(CSV_COLUMNS)} FROM v_listing_cards
            ORDER BY suburb_display, value_mid DESC, id"""
    ).fetchall()
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(CSV_COLUMNS)
        for row in rows:
            writer.writerow([row[col] for col in CSV_COLUMNS])
    return len(rows)


def validate_derived(conn: sqlite3.Connection) -> dict[str, Any]:
    """Fail the build before the DB swap if derived research layers are incomplete.

    The daily pipeline promises that predictions, text features and sale-method
    analysis are refreshed with the listings. Model modules deliberately catch
    individual failures so a transient ML error cannot take down the whole
    build; this check turns a partial derived layer into a fatal, visible error
    instead of publishing stale predictions.
    """
    standard = conn.execute(
        "SELECT COUNT(*) FROM listings WHERE is_standard=1"
    ).fetchone()[0]
    if standard < 50:
        return {"validated": False, "reason": "small test database", "standard": standard}
    checks: dict[str, Any] = {
        "standard": standard,
        "hedonic_predictions": conn.execute(
            "SELECT COUNT(DISTINCT listing_id) FROM model_predictions WHERE model_name='hedonic_avm'"
        ).fetchone()[0],
        "text_eligible": conn.execute(
            "SELECT COUNT(*) FROM listings WHERE is_standard=1 "
            "AND length(trim(coalesce(body,''))) >= 50"
        ).fetchone()[0],
        "text_features": conn.execute("SELECT COUNT(*) FROM text_features").fetchone()[0],
        "text_nulls": conn.execute(
            "SELECT COUNT(*) FROM text_features WHERE description_index IS NULL"
        ).fetchone()[0],
        "topics": conn.execute("SELECT COUNT(*) FROM text_topics").fetchone()[0],
        "model_metrics": conn.execute("SELECT COUNT(*) FROM model_metrics").fetchone()[0],
        "text_metrics": conn.execute("SELECT COUNT(*) FROM text_metrics").fetchone()[0],
        "text_terms": conn.execute("SELECT COUNT(*) FROM text_term_associations").fetchone()[0],
        "sale_stages": conn.execute("SELECT COUNT(*) FROM sale_method_analysis").fetchone()[0],
        "price_dynamics": conn.execute("SELECT COUNT(*) FROM listing_price_dynamics").fetchone()[0],
        "property_sales": conn.execute("SELECT COUNT(*) FROM property_sales").fetchone()[0],
        "tenure_known": conn.execute(
            "SELECT COUNT(*) FROM listings WHERE tenure IS NOT NULL AND tenure != 'unknown'"
        ).fetchone()[0],
        "build_year_known": conn.execute(
            "SELECT COUNT(*) FROM listings WHERE build_year IS NOT NULL"
        ).fetchone()[0],
        "price_history": conn.execute("SELECT COUNT(*) FROM listing_price_history").fetchone()[0],
        "price_history_missing_dates": conn.execute(
            "SELECT COUNT(*) FROM listing_price_history WHERE observed_at IS NULL OR observed_at=''"
        ).fetchone()[0],
    }
    errors = []
    if checks["hedonic_predictions"] < standard:
        errors.append(f"hedonic predictions {checks['hedonic_predictions']}/{standard}")
    if checks["text_features"] < checks["text_eligible"]:
        errors.append(f"text features {checks['text_features']}/{checks['text_eligible']} eligible descriptions")
    if checks["text_nulls"]:
        errors.append(f"{checks['text_nulls']} null description indexes")
    if checks["topics"] < 2:
        errors.append("text topics missing")
    if checks["model_metrics"] < 1:
        errors.append("model metrics missing")
    if checks["text_metrics"] < 1:
        errors.append("text metrics missing")
    if checks["text_terms"] < 1:
        errors.append("term-level text analysis missing")
    if checks["sale_stages"] < 1:
        errors.append("sale-method analysis missing")
    if checks["price_dynamics"] < checks["standard"]:
        errors.append(f"price dynamics {checks['price_dynamics']}/{checks['standard']} listings")
    if checks["price_history"] < checks["price_dynamics"]:
        errors.append("price history missing initial observations")
    if checks["price_history_missing_dates"]:
        errors.append(f"{checks['price_history_missing_dates']} price observations without a date")
    if errors:
        raise RuntimeError("Derived research layers are incomplete: " + "; ".join(errors))
    checks["validated"] = True
    checks["errors"] = []
    return checks


def build(raw_dir: Path = RAW_DIR, db_path: Path = DB_PATH, *, skip_export: bool = False) -> dict[str, Any]:
    listings = load_listing_files(raw_dir)
    homes_profiles = load_homes_profiles(raw_dir)
    if not listings:
        raise SystemExit(f"No listing JSON files found under {raw_dir / 'listings'}")
    first_seen, old_snapshots, previous_listings, old_events = previous_state(db_path)
    tmp_path = db_path.with_suffix(".building.db")
    for suffix in ("", "-wal", "-shm"):
        try:
            Path(str(tmp_path) + suffix).unlink()
        except FileNotFoundError:
            pass
    conn = sqlite3.connect(tmp_path)
    conn.row_factory = sqlite3.Row
    conn.executescript((Path(__file__).parent / "schema.sql").read_text(encoding="utf-8"))

    for suburb in config.SUBURBS:
        conn.execute(
            """INSERT OR REPLACE INTO suburbs
               (slug, name, tm_name, district, group_name, lat, lon, geometry_json)
               VALUES (?,?,?,?,?,?,?,?)""",
            (suburb["slug"], suburb["name"], suburb["tm_name"], suburb["district"],
             suburb["group"], None, None, None),
        )

    listings_count = insert_listings(conn, listings, first_seen, homes_profiles)
    lifecycle_stats = reconcile_inventory(conn, raw_dir, previous_listings, utc_now())
    sales_count = insert_sales(conn, listings)
    property_sales_count = insert_property_sales(conn, listings, homes_profiles, utc_now())
    upsert_listing_properties(conn, listings)
    now = utc_now()
    event_count = generate_events(
        conn, previous_listings, old_events,
        had_previous=bool(previous_listings), now_iso=now,
    )
    restore_snapshots(conn, old_snapshots)
    price_stats = build_price_history(conn, now_iso=now)
    update_suburb_centroids(conn)

    valuation_stats = comps.run(conn, now_iso=now)
    # Health/meta counters describe the active app inventory; historical rows are
    # retained separately and carry their last valuation.
    active_value_counts = {
        row["value_source"]: row["n"]
        for row in conn.execute(
            """SELECT value_source, COUNT(*) AS n FROM listings
               WHERE status='active' GROUP BY value_source"""
        )
    }
    valuation_stats.update({
        "listings": conn.execute(
            "SELECT COUNT(*) FROM listings WHERE status='active'"
        ).fetchone()[0],
        "with_homes_avm": active_value_counts.get("homes_avm", 0),
        "with_comp_model": active_value_counts.get("sold_comps", 0)
        + active_value_counts.get("sold_comps_absolute", 0),
        "with_active_guide": active_value_counts.get("active_suburb_guide", 0),
        "with_sold_median": active_value_counts.get("sold_comps", 0),
        "unavailable": active_value_counts.get("unavailable", 0),
    })
    text_stats = None
    if text_model is not None:
        try:
            text_stats = text_model.run(conn)
        except Exception as exc:  # noqa: BLE001 - text layer must not break the build
            text_stats = {"error": str(exc)[:500]}
    text_term_stats = None
    if text_terms is not None:
        try:
            text_term_stats = text_terms.run(conn)
        except Exception as exc:  # noqa: BLE001 - term layer must not break the build
            text_term_stats = {"error": str(exc)[:500]}
    try:
        sale_stats = sale_method.run(conn, now_iso=now)
    except Exception as exc:  # noqa: BLE001
        sale_stats = {"error": str(exc)[:500]}
    hedonic_stats = None
    if valuation_model is not None:
        try:
            hedonic_stats = valuation_model.run(conn, now_iso=now)
        except Exception as exc:  # noqa: BLE001
            hedonic_stats = {"error": str(exc)[:500]}
    comps.compute_suburb_stats(conn, updated_at=now)
    derived_stats = validate_derived(conn)
    conn.execute(
        """UPDATE listing_snapshots SET value_mid = (
               SELECT value_mid FROM listings l WHERE l.id = listing_snapshots.listing_id
           ) WHERE captured_at = (
               SELECT last_seen_at FROM listings l WHERE l.id = listing_snapshots.listing_id
           )"""
    )
    history_stats = compact_history(conn, now_iso=now)
    conn.commit()

    # Derive run metadata from the actual files rather than trusting an earlier
    # partial search-only manifest.
    captured = sorted(
        item.get("captured_at") for item in listings if item.get("captured_at")
    )
    detail_ok_count = sum(1 for item in listings if item.get("detail_ok"))
    missing_estimate_count = sum(
        1 for item in listings
        if item.get("detail_ok") and not ((item.get("homes") or {}).get("estimate_mid"))
    )
    suburb_counts: dict[str, int] = {}
    for item in listings:
        name = item.get("suburb") or "unknown"
        suburb_counts[name] = suburb_counts.get(name, 0) + 1
    manifest = {
        "started_at": captured[0] if captured else None,
        "finished_at": captured[-1] if captured else None,
        "unique_listings": len(listings),
        "details_ok": detail_ok_count,
        "details_missing_estimate": missing_estimate_count,
        "details_failed": len(listings) - detail_ok_count,
        "suburbs": [
            {"name": name, "collected": count}
            for name, count in sorted(suburb_counts.items())
        ],
    }
    (raw_dir / "summary.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    counts = {
        "listings": conn.execute("SELECT COUNT(*) FROM listings").fetchone()[0],
        "sales": conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0],
        "properties": conn.execute("SELECT COUNT(*) FROM properties").fetchone()[0],
        "schools": conn.execute("SELECT COUNT(*) FROM schools").fetchone()[0],
        "estimate_history": conn.execute("SELECT COUNT(*) FROM estimate_history").fetchone()[0],
        "events": conn.execute("SELECT COUNT(*) FROM listing_events").fetchone()[0],
        "active_listings": conn.execute("SELECT COUNT(*) FROM listings WHERE status='active'").fetchone()[0],
        "delisted_listings": conn.execute("SELECT COUNT(*) FROM listings WHERE status='delisted'").fetchone()[0],
        "model_predictions": conn.execute("SELECT COUNT(*) FROM model_predictions").fetchone()[0],
        "price_history": conn.execute("SELECT COUNT(*) FROM listing_price_history").fetchone()[0],
        "price_dynamics": conn.execute("SELECT COUNT(*) FROM listing_price_dynamics").fetchone()[0],
        "property_sales": conn.execute("SELECT COUNT(*) FROM property_sales").fetchone()[0],
        "tenure_known": conn.execute(
            "SELECT COUNT(*) FROM listings WHERE tenure IS NOT NULL AND tenure != 'unknown'"
        ).fetchone()[0],
        "build_year_known": conn.execute(
            "SELECT COUNT(*) FROM listings WHERE build_year IS NOT NULL"
        ).fetchone()[0],
        "description_changes": conn.execute(
            "SELECT COUNT(*) FROM listing_events WHERE event_type='description_change'"
        ).fetchone()[0],
    }
    conn.execute(
        """INSERT INTO scrape_runs
           (started_at, finished_at, status, suburb_count, listing_count, detail_ok,
            missing_estimate, notes)
           VALUES (?,?,?,?,?,?,?,?)""",
        (
            manifest.get("started_at"), manifest.get("finished_at"), "ok",
            len(config.SUBURBS), manifest.get("unique_listings"), manifest.get("details_ok"),
            manifest.get("details_missing_estimate"),
            json.dumps({
                "built_at": now,
                "model": f"{comps.MODEL_VERSION}+hedonic-avm-v1",
                "events": event_count,
                "price_history": price_stats,
            }),
        ),
    )
    write_meta(
        conn,
        {
            "built_at": now,
            "model_version": f"{comps.MODEL_VERSION}+hedonic-avm-v1",
            "listings": counts["listings"],
            "sales": counts["sales"],
            "valuation": valuation_stats,
            "hedonic": hedonic_stats,
            "text_analysis": text_stats,
            "text_terms": text_term_stats,
            "sale_method": sale_stats,
            "counts": counts,
            "lifecycle": lifecycle_stats,
            "history_policy": history_stats,
            "derived": derived_stats,
            "manifest": {k: manifest.get(k) for k in (
                "started_at", "finished_at", "unique_listings", "details_ok",
                "details_missing_estimate", "details_failed",
            )},
        },
    )
    conn.commit()

    export_count = 0
    if not skip_export:
        export_count = export_csv(conn, EXPORT_DIR / "listings.csv")

    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    conn.close()
    for suffix in ("-wal", "-shm"):
        try:
            Path(str(tmp_path) + suffix).unlink()
        except FileNotFoundError:
            pass
    os.replace(tmp_path, db_path)
    for suffix in ("-wal", "-shm"):
        try:
            Path(str(db_path) + suffix).unlink()
        except FileNotFoundError:
            pass

    digest_path = None
    if not skip_export:
        try:
            from analysis.research_digest import DEFAULT_JSON as DIGEST_JSON, write_digest
            write_digest(db_path)
            digest_path = str(DIGEST_JSON)
        except Exception as exc:  # noqa: BLE001 - digest must not invalidate a valid DB
            print(f"WARN: research digest generation failed: {exc}", file=sys.stderr)

    return {
        "db": str(db_path),
        "listings": counts["listings"],
        "sales": counts["sales"],
        "properties": counts["properties"],
        "schools": counts["schools"],
        "estimate_history": counts["estimate_history"],
        "exported": export_count,
        "valuation": valuation_stats,
        "lifecycle": lifecycle_stats,
        "history_policy": history_stats,
        "price_history": price_stats,
        "derived": derived_stats,
        "digest": digest_path,
        "built_at": now,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the property SQLite database")
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--skip-export", action="store_true")
    args = parser.parse_args(argv)
    result = build(args.raw_dir, args.db, skip_export=args.skip_export)
    print(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
