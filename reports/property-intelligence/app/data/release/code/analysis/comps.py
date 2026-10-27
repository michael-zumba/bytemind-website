"""Transparent comparable-sales valuation for active listings.

Preferred signal is Homes.co.nz's AVM range (extracted from the Trade Me detail page).
This module adds an independent model:

1. Find nearby sold comps with a council CV.
2. Use sale_price / CV as a size-normalised ratio (CV captures land + improvements).
3. Weight by distance, recency, property-type match and same-suburb.
4. Take weighted quartiles of the ratio to produce a range around the subject's CV.

When there are too few comps or the listing has no CV, fall back to a suburb guide built
from active listings' AVM ranges, then to the suburb sold median. Every fallback is
labelled, and the basis JSON is stored for auditability.
"""
from __future__ import annotations

import json
import math
import statistics
from datetime import datetime, timezone
from typing import Any, Iterable

MODEL_VERSION = "comp-cv-v1"
DEFAULT_RADIUS_KM = 3.0
MAX_RADIUS_KM = 5.0
MAX_SALE_AGE_MONTHS = 18


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return ordered[lo]
    return ordered[lo] * (hi - pos) + ordered[hi] * (pos - lo)


def _weighted_quantile(values: list[tuple[float, float]], q: float) -> float | None:
    """values: [(value, weight)]. Weights must be positive."""
    items = sorted((v, w) for v, w in values if w > 0)
    if not items:
        return None
    total = sum(w for _, w in items)
    if total <= 0:
        return None
    target = q * total
    cumulative = 0.0
    for value, weight in items:
        cumulative += weight
        if cumulative >= target:
            return value
    return items[-1][0]


def _median(values: Iterable[float | int | None]) -> float | None:
    clean = [float(v) for v in values if v is not None]
    return statistics.median(clean) if clean else None


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # Equirectangular is plenty for a few kilometres and much faster.
    dlat = (lat2 - lat1) * 111.32
    dlon = (lon2 - lon1) * 111.32 * math.cos(math.radians((lat1 + lat2) / 2))
    return math.hypot(dlat, dlon)


def _type_weight(subject: str | None, comp: str | None) -> float:
    a = (subject or "").strip().lower()
    b = (comp or "").strip().lower()
    if not a or not b:
        return 0.55
    if a == b:
        return 1.0
    related = {("unit", "apartment"), ("apartment", "unit"), ("townhouse", "unit"),
               ("unit", "townhouse"), ("townhouse", "apartment"), ("apartment", "townhouse")}
    if (a, b) in related:
        return 0.65
    return 0.25


def _load_data(conn) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    conn.row_factory = __import__("sqlite3").Row
    listings = [dict(r) for r in conn.execute(
        """SELECT id, suburb_slug, suburb_name, property_type, bedrooms, bathrooms,
                  land_area, floor_area, cv, estimate_low, estimate_mid, estimate_high,
                  estimate_updated_at, estimate_matched, lat, lon, asking_price,
                  tenure, last_seen_at, first_seen_at
           FROM listings ORDER BY id"""
    )]
    sales = [dict(r) for r in conn.execute(
        """SELECT id, property_id, address, suburb, sale_price, sale_date, lat, lon,
                  land_area, floor_area, bedrooms, bathrooms, property_type, cv,
                  estimate_mid
           FROM sales WHERE sale_price IS NOT NULL AND sale_price > 0"""
    )]
    return listings, sales


def _candidate_comps(
    listing: dict[str, Any], sales: list[dict[str, Any]], radius_km: float,
    reference_dt: datetime,
) -> list[dict[str, Any]]:
    lat, lon = listing.get("lat"), listing.get("lon")
    if lat is None or lon is None:
        return []
    out: list[dict[str, Any]] = []
    for sale in sales:
        slat, slon = sale.get("lat"), sale.get("lon")
        if slat is None or slon is None:
            continue
        dist = _haversine_km(lat, lon, slat, slon)
        if dist > radius_km:
            continue
        sale_dt = _parse_dt(sale.get("sale_date"))
        age_months = (reference_dt - sale_dt).days / 30.44 if sale_dt else MAX_SALE_AGE_MONTHS
        if age_months < -1 or age_months > MAX_SALE_AGE_MONTHS:
            continue
        out.append({**sale, "distance_km": dist, "age_months": max(0.0, age_months)})
    return out


def _comp_valuation(
    listing: dict[str, Any], sales: list[dict[str, Any]], reference_dt: datetime
) -> dict[str, Any] | None:
    cv = listing.get("cv")
    if not cv or cv <= 0:
        return None
    for radius in (DEFAULT_RADIUS_KM, MAX_RADIUS_KM):
        comps = _candidate_comps(listing, sales, radius, reference_dt)
        valid: list[tuple[float, float, dict[str, Any]]] = []
        for sale in comps:
            sale_cv = sale.get("cv")
            if not sale_cv or sale_cv <= 0:
                continue
            ratio = sale["sale_price"] / sale_cv
            if not 0.45 <= ratio <= 2.8:
                continue
            distance = max(0.1, sale["distance_km"])
            recency = sale["age_months"]
            weight = math.exp(-distance / 1.4) * math.exp(-recency / 11.0)
            weight *= _type_weight(listing.get("property_type"), sale.get("property_type"))
            if (sale.get("suburb") or "").lower() == (listing.get("suburb_name") or "").lower():
                weight *= 1.15
            if weight > 0:
                valid.append((ratio, weight, sale))
        if len(valid) < 3:
            continue
        ratios = [(r, w) for r, w, _ in valid]
        median_ratio = _weighted_quantile(ratios, 0.5)
        q25 = _weighted_quantile(ratios, 0.25)
        q75 = _weighted_quantile(ratios, 0.75)
        if not median_ratio or not q25 or not q75:
            continue
        n_eff = sum(w for _, w, _ in valid)
        iqr_rel = (q75 - q25) / median_ratio if median_ratio else 1.0
        if n_eff >= 8 and iqr_rel <= 0.25:
            confidence = "high"
        elif n_eff >= 4 and iqr_rel <= 0.45:
            confidence = "medium"
        else:
            confidence = "low"
        low = int(round(cv * q25))
        mid = int(round(cv * median_ratio))
        high = int(round(cv * q75))
        # A very wide range is a low-confidence signal, not a useful high-confidence one.
        return {
            "low": low,
            "mid": mid,
            "high": high,
            "confidence": confidence,
            "source": "sold_comps",
            "n": len(valid),
            "n_eff": round(n_eff, 2),
            "radius_km": radius,
            "median_ratio": round(median_ratio, 4),
            "iqr_ratio": round(iqr_rel, 4),
            "same_suburb": sum(
                1 for _, _, s in valid
                if (s.get("suburb") or "").lower() == (listing.get("suburb_name") or "").lower()
            ),
            "model_version": MODEL_VERSION,
        }
    return None


def _absolute_comp_valuation(
    listing: dict[str, Any], sales: list[dict[str, Any]], reference_dt: datetime
) -> dict[str, Any] | None:
    """Fallback for listings without a usable CV.

    Uses raw nearby sold prices, restricted by bedroom count where possible. It is
    less precise than the CV-normalised model because sold comps do not carry floor
    or land area, so confidence is capped at medium.
    """
    lat, lon = listing.get("lat"), listing.get("lon")
    if lat is None or lon is None:
        return None
    beds = listing.get("bedrooms")
    candidates: list[tuple[float, float, dict[str, Any]]] = []
    for sale in sales:
        slat, slon = sale.get("lat"), sale.get("lon")
        if slat is None or slon is None:
            continue
        dist = _haversine_km(lat, lon, slat, slon)
        if dist > 3.0:
            continue
        sale_dt = _parse_dt(sale.get("sale_date"))
        age_months = (reference_dt - sale_dt).days / 30.44 if sale_dt else MAX_SALE_AGE_MONTHS
        if age_months < -1 or age_months > MAX_SALE_AGE_MONTHS:
            continue
        if beds is not None and sale.get("bedrooms") is not None and abs(sale["bedrooms"] - beds) > 1:
            continue
        price = sale.get("sale_price")
        if not price or price <= 0:
            continue
        weight = math.exp(-max(0.1, dist) / 1.4) * math.exp(-max(0.0, age_months) / 11.0)
        if (sale.get("suburb") or "").lower() == (listing.get("suburb_name") or "").lower():
            weight *= 1.15
        candidates.append((float(price), weight, sale))
    if len(candidates) < 4:
        return None
    q25 = _weighted_quantile([(v, w) for v, w, _ in candidates], 0.25)
    med = _weighted_quantile([(v, w) for v, w, _ in candidates], 0.5)
    q75 = _weighted_quantile([(v, w) for v, w, _ in candidates], 0.75)
    if not q25 or not med or not q75:
        return None
    n_eff = sum(w for _, w, _ in candidates)
    iqr_rel = (q75 - q25) / med if med else 1.0
    confidence = "medium" if n_eff >= 8 and iqr_rel <= 0.35 else "low"
    return {
        "low": int(round(q25)),
        "mid": int(round(med)),
        "high": int(round(q75)),
        "confidence": confidence,
        "source": "sold_comps_absolute",
        "n": len(candidates),
        "n_eff": round(n_eff, 2),
        "radius_km": 3.0,
        "iqr_ratio": round(iqr_rel, 4),
        "same_suburb": sum(
            1 for _, _, s in candidates
            if (s.get("suburb") or "").lower() == (listing.get("suburb_name") or "").lower()
        ),
        "model_version": MODEL_VERSION,
    }


def _suburb_guide(
    listings: list[dict[str, Any]], target: dict[str, Any]
) -> dict[str, Any] | None:
    """Fallback from active-listings' AVM values in the same suburb."""
    suburb = target.get("suburb_slug")
    prop_type = (target.get("property_type") or "").lower()
    beds = target.get("bedrooms")
    same_suburb = [
        x for x in listings
        if x.get("suburb_slug") == suburb and x.get("estimate_mid") and x["id"] != target["id"]
    ]
    if not same_suburb:
        return None

    def pick(group: list[dict[str, Any]], label: str) -> dict[str, Any] | None:
        if len(group) < 3:
            return None
        values = [x["estimate_mid"] for x in group]
        mid = _median(values)
        if mid is None:
            return None
        q25 = _quantile(values, 0.25)
        q75 = _quantile(values, 0.75)
        return {
            "low": int(round(q25 or mid)),
            "mid": int(round(mid)),
            "high": int(round(q75 or mid)),
            "confidence": "low",
            "source": "active_suburb_guide",
            "n": len(group),
            "basis": label,
            "model_version": MODEL_VERSION,
        }

    typed = [x for x in same_suburb if (x.get("property_type") or "").lower() == prop_type]
    if beds is not None:
        nearby_beds = [x for x in typed if x.get("bedrooms") is not None and abs(x["bedrooms"] - beds) <= 1]
        result = pick(nearby_beds, "same suburb, same type, beds +/-1")
        if result:
            return result
    result = pick(typed, "same suburb, same type")
    if result:
        return result
    return pick(same_suburb, "same suburb, all types")


def _sold_median_guide(sales: list[dict[str, Any]], target: dict[str, Any]) -> dict[str, Any] | None:
    suburb = (target.get("suburb_name") or "").lower()
    values = [
        s["sale_price"] for s in sales
        if (s.get("suburb") or "").lower() == suburb and s.get("sale_price")
    ]
    if len(values) < 3:
        return None
    mid = _median(values)
    if not mid:
        return None
    return {
        "low": int(round(_quantile(values, 0.25) or mid)),
        "mid": int(round(mid)),
        "high": int(round(_quantile(values, 0.75) or mid)),
        "confidence": "low",
        "source": "suburb_sold_median",
        "n": len(values),
        "model_version": MODEL_VERSION,
    }


def compute_valuations(conn, *, now_iso: str | None = None) -> dict[str, Any]:
    now_iso = now_iso or datetime.now(timezone.utc).isoformat()
    reference = _parse_dt(now_iso) or datetime.now(timezone.utc)
    listings, sales = _load_data(conn)

    stats = {
        "listings": len(listings),
        "with_homes_avm": 0,
        "with_comp_model": 0,
        "with_active_guide": 0,
        "with_sold_median": 0,
        "unavailable": 0,
        "model_version": MODEL_VERSION,
        "computed_at": now_iso,
    }

    updates: list[tuple[Any, ...]] = []
    for listing in listings:
        comp = _comp_valuation(listing, sales, reference)
        if comp is None:
            comp = _absolute_comp_valuation(listing, sales, reference)
        value: dict[str, Any] | None = None
        value_basis: dict[str, Any] = {}

        if listing.get("estimate_mid"):
            value = {
                "low": listing.get("estimate_low"),
                "mid": listing.get("estimate_mid"),
                "high": listing.get("estimate_high"),
                "confidence": "high" if listing.get("estimate_matched") else "medium",
                "source": "homes_avm",
            }
            updated = _parse_dt(listing.get("estimate_updated_at"))
            if updated and (reference - updated).days > 120:
                value["confidence"] = "medium"
            stats["with_homes_avm"] += 1
        elif comp:
            value = comp
            stats["with_comp_model"] += 1
        else:
            guide = _suburb_guide(listings, listing)
            if guide:
                value = guide
                stats["with_active_guide"] += 1
            else:
                sold = _sold_median_guide(sales, listing)
                if sold:
                    value = sold
                    stats["with_sold_median"] += 1

        if value:
            value_low = value.get("low")
            value_mid = value.get("mid")
            value_high = value.get("high")
            value_source = value.get("source")
            value_confidence = value.get("confidence")
            value_basis = {"primary": value, "comp_model": comp}
        else:
            value_low = value_mid = value_high = None
            value_source = "unavailable"
            value_confidence = "none"
            value_basis = {"comp_model": comp, "reason": "no AVM, no comps and no suburb guide"}
            stats["unavailable"] += 1

        cv = listing.get("cv")
        cv_ratio = round(value_mid / cv, 4) if value_mid and cv else None
        asking = listing.get("asking_price")
        # Only expose an asking-price gap when the underlying value signal is
        # strong enough to make the comparison meaningful.
        reliable_value = (
            bool(value_mid)
            and value_confidence in {"high", "medium"}
            and (listing.get("tenure") or "").lower() != "leasehold"
        )
        ask_gap = round((asking - value_mid) / value_mid, 4) if asking and reliable_value else None
        deal_gap = round((value_mid - asking) / value_mid, 4) if asking and reliable_value else None

        comp_low = comp.get("low") if comp else None
        comp_mid = comp.get("mid") if comp else None
        comp_high = comp.get("high") if comp else None
        comp_conf = comp.get("confidence") if comp else None
        comp_source = comp.get("source") if comp else None
        comp_n = comp.get("n") if comp else None
        comp_basis = {k: v for k, v in comp.items() if k not in {"low", "mid", "high"}} if comp else None

        updates.append((
            value_low, value_mid, value_high, value_source, value_confidence,
            json.dumps(value_basis, ensure_ascii=False),
            comp_low, comp_mid, comp_high, comp_conf, comp_source, comp_n,
            json.dumps(comp_basis, ensure_ascii=False) if comp_basis else None,
            cv_ratio, ask_gap, deal_gap, listing["id"],
        ))

    conn.executemany(
        """UPDATE listings SET
             value_low=?, value_mid=?, value_high=?, value_source=?, value_confidence=?,
             value_basis_json=?,
             comp_low=?, comp_mid=?, comp_high=?, comp_confidence=?, comp_source=?,
             comp_n=?, comp_basis_json=?,
             cv_ratio=?, ask_gap=?, deal_gap=?
           WHERE id=?""",
        updates,
    )
    conn.commit()
    return stats


def compute_suburb_stats(conn, *, updated_at: str | None = None) -> None:
    updated_at = updated_at or datetime.now(timezone.utc).isoformat()
    conn.row_factory = __import__("sqlite3").Row
    rows = [dict(r) for r in conn.execute("SELECT * FROM listings")]
    sales = [dict(r) for r in conn.execute(
        "SELECT * FROM sales WHERE sale_price > 0"
    )]
    for suburb in [dict(r) for r in conn.execute("SELECT * FROM suburbs ORDER BY name")]:
        slug = suburb["slug"]
        group = [
            r for r in rows
            if r["suburb_slug"] == slug and (r.get("is_standard") or 0) == 1
            and r.get("status") == "active"
        ]
        if not group:
            continue
        values = [r["value_mid"] for r in group if r["value_mid"]]
        asks = [r["asking_price"] for r in group if r["asking_price"]]
        cvs = [r["cv"] for r in group if r["cv"]]
        lands = [r["land_area"] for r in group if r["land_area"]]
        floors = [r["floor_area"] for r in group if r["floor_area"]]
        doms = [r["days_on_market"] for r in group if r["days_on_market"] is not None]
        ratios = [r["cv_ratio"] for r in group if r["cv_ratio"]]
        sold = [
            s for s in sales
            if (s.get("suburb") or "").lower() == (suburb["name"] or "").lower()
        ]
        sold_prices = [s["sale_price"] for s in sold if s["sale_price"]]
        sold_ratios = [
            s["sale_price"] / s["cv"] for s in sold if s.get("cv") and s["cv"] > 0
        ]
        conn.execute(
            """INSERT INTO suburb_stats (
                 suburb_slug, active_count, median_value, median_asking, median_cv,
                 median_land, median_floor, median_dom, min_value, max_value,
                 avm_cv_ratio, median_sold, median_sold_cv_ratio, sold_count, updated_at
               ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(suburb_slug) DO UPDATE SET
                 active_count=excluded.active_count, median_value=excluded.median_value,
                 median_asking=excluded.median_asking, median_cv=excluded.median_cv,
                 median_land=excluded.median_land, median_floor=excluded.median_floor,
                 median_dom=excluded.median_dom, min_value=excluded.min_value,
                 max_value=excluded.max_value, avm_cv_ratio=excluded.avm_cv_ratio,
                 median_sold=excluded.median_sold,
                 median_sold_cv_ratio=excluded.median_sold_cv_ratio,
                 sold_count=excluded.sold_count, updated_at=excluded.updated_at""",
            (
                slug, len(group), _int_median(values), _int_median(asks), _int_median(cvs),
                _median(lands), _median(floors), round(statistics.median(doms), 1) if doms else None,
                min(values) if values else None, max(values) if values else None,
                round(_median(ratios), 4) if ratios else None,
                _int_median(sold_prices),
                round(_median(sold_ratios), 4) if sold_ratios else None,
                len(sold), updated_at,
            ),
        )
    conn.commit()


def _int_median(values: Iterable[float | int | None]) -> int | None:
    mid = _median(values)
    return int(round(mid)) if mid is not None else None


def run(conn, *, now_iso: str | None = None) -> dict[str, Any]:
    stats = compute_valuations(conn, now_iso=now_iso)
    compute_suburb_stats(conn, updated_at=now_iso)
    return stats
