"""Pure parsing helpers for Trade Me search JSON and SSR detail state.

Keeping these functions pure makes the collector testable with small fixtures.
"""
from __future__ import annotations

import html as html_module
import json
import math
import re
from datetime import datetime, timezone, date
from typing import Any

MONEY_RE = re.compile(r"\$?\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*([kKmM])?")
DATE_MS_RE = re.compile(r"/Date\((-?\d+)\)/")


# --------------------------------------------------------------------------- primitives
def parse_date(value: Any) -> str | None:
    """Normalise Trade Me's several date encodings to an ISO-8601 UTC string."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value / 1000, tz=timezone.utc).isoformat()
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=timezone.utc).isoformat()
    text = str(value).strip()
    if text.startswith("__date__:"):
        text = text[len("__date__:"):].strip()
    m = DATE_MS_RE.fullmatch(text)
    if m:
        return datetime.fromtimestamp(int(m.group(1)) / 1000, tz=timezone.utc).isoformat()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def parse_money(value: Any) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(round(value))
    text = str(value).strip()
    if not text or text.lower() in {"none", "null", "n/a", "-"}:
        return None
    low = text.lower()
    if "reserve" in low and "$1" in low:
        return None
    m = MONEY_RE.search(text.replace(",", ""))
    if not m:
        return None
    number = float(m.group(1))
    suffix = (m.group(2) or "").lower()
    if suffix == "m":
        number *= 1_000_000
    elif suffix == "k":
        number *= 1_000
    if number < 1000:  # avoid interpreting "$1 reserve" or odd tiny values as prices
        return None
    return int(round(number))


def money_tokens(text: str | None) -> list[int]:
    if not text:
        return []
    tokens: list[int] = []
    for m in MONEY_RE.finditer(text.replace(",", "")):
        number = float(m.group(1))
        suffix = (m.group(2) or "").lower()
        if suffix == "m":
            number *= 1_000_000
        elif suffix == "k":
            number *= 1_000
        if number >= 1000:
            tokens.append(int(round(number)))
    return tokens


def parse_range_display(text: str | None) -> tuple[int | None, int | None, int | None]:
    """Parse "$1.2M - $1.34M" into (low, mid, high)."""
    tokens = money_tokens(text)
    if not tokens:
        return None, None, None
    if len(tokens) == 1:
        return tokens[0], tokens[0], tokens[0]
    low, high = min(tokens[0], tokens[1]), max(tokens[0], tokens[1])
    return low, int(round((low + high) / 2)), high


def parse_asking_price(price_display: str | None) -> tuple[int | None, str | None]:
    """Return (advertised price, kind) from a Trade Me price string.

    Auction/tender displays normally have no price. If a price is present it is a
    genuine advertised guide, so we keep it even when the sale method is a deadline.
    """
    if not price_display:
        return None, None
    low = price_display.lower()
    if "reserve" in low and "$1" in low:
        return None, None
    tokens = money_tokens(price_display)
    if not tokens:
        return None, None
    price = min(tokens) if len(tokens) > 1 else tokens[0]
    if "enquir" in low or "over" in low or "from" in low:
        return price, "enquiries_over"
    if "guide" in low:
        return price, "price_guide"
    return price, "asking"


def infer_sale_method(price_display: str | None, sale_info: dict[str, Any] | None = None) -> str:
    text = (price_display or "").lower()
    sale_info = sale_info or {}
    sale_type = sale_info.get("PropertySaleType") or sale_info.get("propertySaleType")
    if "auction" in text:
        return "auction"
    if "tender" in text:
        return "tender"
    if "deadline" in text:
        return "deadline"
    if "negotiat" in text:
        return "negotiation"
    if "$" in (price_display or ""):
        return "asking"
    type_map = {1: "asking", 3: "auction", 4: "tender", 5: "negotiation", 7: "deadline"}
    return type_map.get(int(sale_type), "other") if sale_type is not None else "other"


def parse_deadline(price_display: str | None, sale_info: dict[str, Any] | None) -> str | None:
    method = infer_sale_method(price_display, sale_info)
    if method not in {"auction", "tender", "deadline"}:
        return None
    raw = (sale_info or {}).get("PropertyDateOfSale") or (sale_info or {}).get("propertyDateOfSale")
    return parse_date(raw)


def _int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def extract_area(value: Any) -> float | None:
    """Parse '208m²', '1,012 m2', 208 into square metres."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    m = re.search(r"([0-9][0-9,]*(?:\.[0-9]+)?)", str(value).replace(",", ""))
    return float(m.group(1)) if m else None


# --------------------------------------------------------------------------- search API
def parse_search_item(item: dict[str, Any], *, target_suburb: dict[str, str] | None = None) -> dict[str, Any]:
    price_display = item.get("PriceDisplay") or ""
    sale_info = item.get("PropertySaleInformation") or {}
    asking_price, asking_kind = parse_asking_price(price_display)
    geo = item.get("GeographicLocation") or {}
    listing_id = _int(item.get("ListingId"))
    canonical_path = item.get("CanonicalPath") or ""
    picture = item.get("PictureHref") or ""
    photo_url = picture.replace("/thumb/", "/med/") if picture else None
    suburb_name = item.get("Suburb") or (target_suburb or {}).get("tm_name") or ""
    display_suburb = (target_suburb or {}).get("name") or suburb_name
    address = (item.get("Address") or "").strip()
    return {
        "listing_id": listing_id,
        "title": (item.get("Title") or "").strip(),
        "address": address,
        "suburb": display_suburb,
        "tm_suburb": suburb_name,
        "district": item.get("District") or "",
        "region": item.get("Region") or "Auckland",
        "property_type": item.get("PropertyType") or "",
        "bedrooms": _int(item.get("Bedrooms")),
        "bathrooms": _int(item.get("Bathrooms")),
        "lounges": _int(item.get("Lounges")),
        "parking": _int(item.get("TotalParking") or item.get("Parking")),
        "land_area": _float(item.get("LandArea")),
        "floor_area": _float(item.get("Area")),
        "price_display": price_display.strip(),
        "asking_price": asking_price,
        "asking_kind": asking_kind,
        "sale_method": infer_sale_method(price_display, sale_info),
        "deadline_at": parse_deadline(price_display, sale_info),
        "listed_at": parse_date(item.get("StartDate")),
        "end_at": parse_date(item.get("EndDate")),
        "as_at": parse_date(item.get("AsAt")),
        "lat": _float(geo.get("Latitude")),
        "lon": _float(geo.get("Longitude")),
        "canonical_path": canonical_path,
        "url": f"https://www.trademe.co.nz/a{canonical_path}" if canonical_path else None,
        "photo_url": photo_url,
        "member_id": _int(item.get("MemberId")),
        "agency_reference": item.get("AgencyReference"),
        "is_featured": bool(item.get("IsFeatured")),
        "suburb_slug": (target_suburb or {}).get("slug"),
        "detail_ok": False,
        "detail_error": None,
    }


# --------------------------------------------------------------------------- detail state
def parse_state(html: str) -> dict[str, Any]:
    m = re.search(
        r'<script id="frend-state" type="application/json">(.*?)</script>', html, re.S
    )
    if not m:
        raise ValueError("frend-state not found")
    raw = html_module.unescape(m.group(1))
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        payload = json.loads(m.group(1))
    # Angular persists the whole transfer state; the app's slices live under NGRX_STATE.
    if isinstance(payload, dict) and isinstance(payload.get("NGRX_STATE"), dict):
        return payload["NGRX_STATE"]
    return payload


def _find_entity_item(state: dict[str, Any], key_fragment: str, listing_id: int) -> dict[str, Any] | None:
    for key, value in state.items():
        if key_fragment not in key or not isinstance(value, dict):
            continue
        entity_maps: list[dict[str, Any]] = []
        if isinstance(value.get("entities"), dict):
            entity_maps.append(value["entities"])
        for nested in value.values():
            if isinstance(nested, dict) and isinstance(nested.get("entities"), dict):
                entity_maps.append(nested["entities"])
        for entities in entity_maps:
            entry = entities.get(str(listing_id)) or entities.get(listing_id)
            if isinstance(entry, dict) and isinstance(entry.get("item"), dict):
                return entry["item"]
    return None


def _find_nearby_item(state: dict[str, Any]) -> dict[str, Any] | None:
    for key, value in state.items():
        if "NearbySalesSearch" not in key:
            continue
        entities = value.get("nearbySalesSearchStateEntities", {}).get("entities", {})
        if not entities:
            continue
        first = next(iter(entities.values()))
        if isinstance(first, dict) and isinstance(first.get("item"), dict):
            return first["item"]
    return None


def _find_detail_item(state: dict[str, Any], listing_id: int) -> dict[str, Any] | None:
    listing = state.get("listing") or {}
    details = listing.get("cachedDetails") or {}
    entities = details.get("entities") or {}
    entry = entities.get(str(listing_id)) or entities.get(listing_id)
    if isinstance(entry, dict) and isinstance(entry.get("item"), dict):
        return entry["item"]
    return None


def parse_detail_item(item: dict[str, Any]) -> dict[str, Any]:
    photos: list[str] = []
    for photo in item.get("photos") or []:
        value = photo.get("value") if isinstance(photo, dict) else None
        if isinstance(value, dict):
            url = value.get("large") or value.get("gallery") or value.get("medium") or value.get("list")
            if url:
                photos.append(url)
    agency = item.get("agency") or {}
    member = item.get("member") or {}
    attrs = {
        (a.get("name") or "").lower(): a.get("value")
        for a in (item.get("propertyAttributes") or [])
        if isinstance(a, dict)
    }
    return {
        "title": (item.get("title") or "").strip(),
        "body": (item.get("body") or "").strip(),
        "photos": photos[:24],
        "phone_number": agency.get("phoneNumber"),
        "agency_name": agency.get("name"),
        "agency_website": agency.get("website"),
        "agency_id": agency.get("id"),
        "member_nickname": member.get("nickname"),
        "view_count": _int(item.get("viewCount")),
        "watchers": _int(item.get("bidderAndWatchers")),
        "attributes": attrs,
        "land_area": extract_area(attrs.get("land_area")),
        "floor_area": extract_area(attrs.get("floor_area")),
        "property_type": attrs.get("property_type"),
        "bedrooms": _int(attrs.get("bedrooms")),
        "bathrooms": _int(attrs.get("bathrooms")),
        "lounges": _int(attrs.get("lounges")),
        "parking": _int(attrs.get("garage_parking") or attrs.get("parking")),
        "listed_at": parse_date(item.get("startDate")),
        "end_at": parse_date(item.get("endDate")),
        "price_display": (item.get("priceDisplay") or "").strip(),
        "sale_method": infer_sale_method(item.get("priceDisplay"), item.get("propertySaleInformation")),
        "deadline_at": parse_deadline(item.get("priceDisplay"), item.get("propertySaleInformation")),
        "lat": _float((item.get("geographicLocation") or {}).get("latitude")),
        "lon": _float((item.get("geographicLocation") or {}).get("longitude")),
    }


def parse_estimate(item: dict[str, Any]) -> dict[str, Any]:
    estimate = item.get("propertyEstimate") or {}
    capital = item.get("capitalValue") or {}
    trends = item.get("propertyTrends") or {}
    history_data = ((trends.get("propertyEstimateHistory") or {}).get("data") or [])
    suburb_data = ((trends.get("suburbEstimateHistory") or {}).get("data") or [])

    history: list[dict[str, Any]] = []
    for row in history_data:
        low = _float(row.get("lowEstimate"))
        mid = _float(row.get("estimate"))
        high = _float(row.get("highEstimate"))
        history.append(
            {
                "date": parse_date(row.get("date")),
                "estimate_low": int(round(low)) if low is not None else None,
                "estimate_mid": int(round(mid)) if mid is not None else None,
                "estimate_high": int(round(high)) if high is not None else None,
                "display": row.get("estimateDisplay"),
            }
        )
    # Latest point is authoritative; the display range is the fallback.
    latest = history[-1] if history else None
    disp_low, disp_mid, disp_high = parse_range_display(
        estimate.get("estimatedMarketPriceRangeDisplay")
    )
    low = latest.get("estimate_low") if latest else disp_low
    mid = latest.get("estimate_mid") if latest else disp_mid
    high = latest.get("estimate_high") if latest else disp_high

    cv = parse_money(capital.get("capitalValueDisplay"))
    if cv is None:
        for event in item.get("propertyEvents") or []:
            if event.get("type") == "valuation":
                cv = _int((event.get("valuation") or {}).get("capitalValue"))
    build_decade = None
    for event in item.get("propertyEvents") or []:
        if event.get("type") == "built":
            build_decade = (event.get("built") or {}).get("decadeBuilt")
            break

    suburb_history = [
        {
            "date": parse_date(row.get("date")),
            "estimate_mid": int(round(_float(row.get("estimate")) or 0)) or None,
        }
        for row in suburb_data
        if row.get("estimate") is not None
    ]

    return {
        "matched": bool(item.get("isMatched")),
        "property_id": item.get("propertyId"),
        "homes_url": item.get("fullDetailPageUrl"),
        "estimate_display": estimate.get("estimatedMarketPriceRangeDisplay"),
        "estimate_low": low,
        "estimate_mid": mid,
        "estimate_high": high,
        "estimate_updated_at": parse_date(estimate.get("updatedDate")),
        "estimate_model_version": item.get("estimateModelVersion"),
        "estimate_model_release_date": item.get("estimateModelReleaseDate"),
        "cv": cv,
        "land_value": parse_money(capital.get("landValueDisplay")),
        "improvement_value": parse_money(capital.get("improvementValueDisplay")),
        "cv_updated_at": parse_date(capital.get("updatedDate")),
        "build_decade": build_decade,
        "history": history,
        "suburb_history": suburb_history,
    }


def parse_nearby_sales(item: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not item:
        return []
    cards = item.get("cards") or []
    comps: list[dict[str, Any]] = []
    seen: set[str] = set()
    for card in cards:
        details = card.get("propertyDetails") or {}
        price = _int(card.get("price"))
        if not price:
            price = parse_money(card.get("displayPrice"))
        if not price:
            continue
        key = str(card.get("propertyId") or details.get("address") or "")
        if key in seen:
            continue
        seen.add(key)
        point = card.get("point") or {}
        distance = _float(card.get("distanceToPoint"))
        comps.append(
            {
                "property_id": card.get("propertyId"),
                "address": details.get("displayAddress") or details.get("address"),
                "sale_price": price,
                "sale_date": parse_date(card.get("date")),
                "distance_km": round(distance / 1000, 3) if distance is not None else None,
                "lat": _float(point.get("lat")),
                "lon": _float(point.get("lon") or point.get("long")),
                "bedrooms": _int(details.get("numBedrooms") or details.get("latestBedrooms")),
                "bathrooms": _int(details.get("numBathrooms") or details.get("latestBathrooms")),
                "car_spaces": _int(details.get("numCarSpaces") or details.get("latestCarSpaces")),
                "land_area": _float(details.get("landArea")),
                "floor_area": _float(details.get("floorArea")),
                "property_type": details.get("propertyType"),
                "cv": _int(details.get("capitalValue")),
                "land_value": _int(details.get("landValue")),
                "improvement_value": _int(details.get("improvementValue")),
                "cv_updated_at": parse_date(details.get("currentRevisionDate")),
                "estimate_mid": parse_money(details.get("displayEstimatedValueShort")),
                "estimate_low": parse_money(details.get("displayEstimatedLowerValueShort")),
                "estimate_high": parse_money(details.get("displayEstimatedUpperValueShort")),
                "sale_count": _int(card.get("salesCount")),
                "source": "trademe_nearby_sales",
            }
        )
    return comps


def parse_schools(payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not payload:
        return []
    out: list[dict[str, Any]] = []
    for school in payload.get("Schools") or []:
        location = school.get("Location") or {}
        zones = school.get("Zones") or []
        in_zone = any(bool(z.get("InZone")) for z in zones) if zones else None
        decile = school.get("Decile") or school.get("decile")
        out.append(
            {
                "school_id": school.get("SchoolId"),
                "name": school.get("Name"),
                "type": school.get("InstitutionType"),
                "authority": school.get("Authority"),
                "roll": _int(school.get("SchoolRoll")),
                "gender": school.get("GenderDescription"),
                "decile": _int(decile),
                "address": school.get("StreetAddress"),
                "suburb": school.get("Suburb"),
                "lat": _float(location.get("Latitude")),
                "lon": _float(location.get("Longitude")),
                "in_zone": in_zone,
            }
        )
    out.sort(key=lambda s: (s["in_zone"] is not True, s["name"] or ""))
    return out


# --------------------------------------------------------------------------- merge
def merge_listing(
    basic: dict[str, Any],
    *,
    detail_state: dict[str, Any] | None = None,
    schools_payload: dict[str, Any] | None = None,
    captured_at: str | None = None,
) -> dict[str, Any]:
    listing = dict(basic)
    listing_id = int(listing["listing_id"])
    listing["captured_at"] = captured_at or datetime.now(timezone.utc).isoformat()
    listing["detail_ok"] = False
    listing["detail_error"] = None
    listing["homes"] = {
        "matched": False,
        "estimate_low": None,
        "estimate_mid": None,
        "estimate_high": None,
        "cv": None,
        "history": [],
        "suburb_history": [],
    }
    listing["comps"] = []
    listing["schools"] = parse_schools(schools_payload)
    listing["photos"] = []

    if not detail_state:
        return listing
    detail_item = _find_detail_item(detail_state, listing_id)
    if not detail_item:
        listing["detail_error"] = "detail item missing from state"
        return listing
    detail = parse_detail_item(detail_item)
    listing["detail_ok"] = True
    listing["detail_error"] = None
    listing["detail"] = detail
    listing["title"] = detail["title"] or listing["title"]
    listing["body"] = detail["body"]
    listing["photos"] = detail["photos"]
    listing["agency_name"] = detail["agency_name"]
    listing["agency_phone"] = detail["phone_number"]
    listing["agency_website"] = detail["agency_website"]
    listing["member_nickname"] = detail["member_nickname"]
    listing["view_count"] = detail["view_count"]
    listing["watchers"] = detail["watchers"]
    listing["price_display"] = detail["price_display"] or listing["price_display"]
    asking, asking_kind = parse_asking_price(listing["price_display"])
    listing["asking_price"] = asking
    listing["asking_kind"] = asking_kind
    listing["sale_method"] = detail["sale_method"]
    listing["deadline_at"] = detail["deadline_at"]
    listing["listed_at"] = detail["listed_at"] or listing["listed_at"]
    listing["end_at"] = detail["end_at"] or listing["end_at"]
    listing["lat"] = detail["lat"] or listing["lat"]
    listing["lon"] = detail["lon"] or listing["lon"]
    for field in ("land_area", "floor_area", "bedrooms", "bathrooms", "lounges", "parking"):
        if listing.get(field) is None and detail.get(field) is not None:
            listing[field] = detail[field]
    if detail.get("property_type"):
        listing["property_type"] = detail["property_type"]

    estimate_item = _find_entity_item(detail_state, "PropertyEstimate", listing_id)
    if estimate_item:
        listing["homes"] = parse_estimate(estimate_item)
    listing["comps"] = parse_nearby_sales(_find_nearby_item(detail_state))

    # Convenience derived values used throughout the app.
    homes = listing["homes"]
    estimate_mid = homes.get("estimate_mid")
    cv = homes.get("cv")
    listing["estimate_mid"] = estimate_mid
    listing["cv"] = cv
    listing["cv_ratio"] = round(estimate_mid / cv, 4) if estimate_mid and cv else None
    if listing.get("lat") is not None and listing.get("lon") is not None:
        if not (-38 < listing["lat"] < -34) or not (172 < listing["lon"] < 179):
            listing["detail_error"] = "coordinates outside New Zealand bounds"
    return listing


def days_on_market(listed_at: str | None, captured_at: str | None) -> int | None:
    if not listed_at or not captured_at:
        return None
    try:
        start = datetime.fromisoformat(listed_at)
        end = datetime.fromisoformat(captured_at)
    except ValueError:
        return None
    return max(0, (end - start).days)
