"""Shared configuration for the Trade Me collector."""
from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
SEARCH_DIR = RAW_DIR / "search"
LISTING_DIR = RAW_DIR / "listings"
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"

for _p in (DATA_DIR, RAW_DIR, SEARCH_DIR, LISTING_DIR, FIXTURE_DIR):
    _p.mkdir(parents=True, exist_ok=True)

# The 17 target suburbs. `tm_name` is the name Trade Me returns; `name` is what we show
# in the UI. St Heliers is listed as "Saint Heliers" on Trade Me.
SUBURBS: list[dict[str, str]] = [
    {"name": "Browns Bay", "tm_name": "Browns Bay", "slug": "browns-bay", "district": "north-shore-city", "group": "North Shore"},
    {"name": "Murrays Bay", "tm_name": "Murrays Bay", "slug": "murrays-bay", "district": "north-shore-city", "group": "North Shore"},
    {"name": "Mairangi Bay", "tm_name": "Mairangi Bay", "slug": "mairangi-bay", "district": "north-shore-city", "group": "North Shore"},
    {"name": "Rothesay Bay", "tm_name": "Rothesay Bay", "slug": "rothesay-bay", "district": "north-shore-city", "group": "North Shore"},
    {"name": "Campbells Bay", "tm_name": "Campbells Bay", "slug": "campbells-bay", "district": "north-shore-city", "group": "North Shore"},
    {"name": "Castor Bay", "tm_name": "Castor Bay", "slug": "castor-bay", "district": "north-shore-city", "group": "North Shore"},
    {"name": "Milford", "tm_name": "Milford", "slug": "milford", "district": "north-shore-city", "group": "North Shore"},
    {"name": "Long Bay", "tm_name": "Long Bay", "slug": "long-bay", "district": "north-shore-city", "group": "North Shore"},
    {"name": "Waiake", "tm_name": "Waiake", "slug": "waiake", "district": "north-shore-city", "group": "North Shore"},
    {"name": "Torbay", "tm_name": "Torbay", "slug": "torbay", "district": "north-shore-city", "group": "North Shore"},
    {"name": "Takapuna", "tm_name": "Takapuna", "slug": "takapuna", "district": "north-shore-city", "group": "North Shore"},
    {"name": "Devonport", "tm_name": "Devonport", "slug": "devonport", "district": "north-shore-city", "group": "North Shore"},
    {"name": "Mission Bay", "tm_name": "Mission Bay", "slug": "mission-bay", "district": "auckland-city", "group": "East"},
    {"name": "Kohimarama", "tm_name": "Kohimarama", "slug": "kohimarama", "district": "auckland-city", "group": "East"},
    {"name": "St Heliers", "tm_name": "Saint Heliers", "slug": "saint-heliers", "district": "auckland-city", "group": "East"},
    {"name": "Glendowie", "tm_name": "Glendowie", "slug": "glendowie", "district": "auckland-city", "group": "East"},
    {"name": "Ōrākei", "tm_name": "Orakei", "slug": "orakei", "district": "auckland-city", "group": "East"},
]

SUBURB_BY_SLUG = {s["slug"]: s for s in SUBURBS}
SUBURB_BY_NAME = {s["name"]: s for s in SUBURBS}

API_BASE = "https://api.trademe.co.nz/v1"
WEB_BASE = "https://www.trademe.co.nz"

USER_AGENT = os.environ.get(
    "APR_USER_AGENT",
    "AucklandPropertyResearch/1.0 (personal property research; low-volume, cached)",
)

JSON_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-NZ,en;q=0.9",
    "Origin": WEB_BASE,
    "Referer": f"{WEB_BASE}/",
}

HTML_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-NZ,en;q=0.9",
    "sec-ch-ua": '"Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

# Politeness controls. Global spacing between any two network calls.
REQUEST_SPACING_SECONDS = float(os.environ.get("APR_REQUEST_SPACING", "0.35"))
MAX_WORKERS = int(os.environ.get("APR_MAX_WORKERS", "2"))
REQUEST_TIMEOUT = 40
MAX_RETRIES = 4

# Re-use cached search responses for this long.
SEARCH_CACHE_HOURS = 12
# Re-use a fully parsed listing for this long when resuming.
LISTING_CACHE_HOURS = 24
