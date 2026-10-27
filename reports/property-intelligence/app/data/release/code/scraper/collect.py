"""Collect Trade Me inventory for the target suburbs.

Examples
--------
Search all suburbs and fetch every detail page (resumable)::

    python -m scraper.collect

Search only, for a quick inventory count::

    python -m scraper.collect --only-search

Smoke test on a few listings::

    python -m scraper.collect --suburbs browns-bay --limit 5 --force
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import config
from .parse import merge_listing, parse_schools, parse_search_item, parse_state
from .trademe import TradeMeClient, TradeMeError, utc_now

log = logging.getLogger("scraper.collect")


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_suburbs(values: list[str] | None) -> list[dict[str, str]]:
    if not values or values == ["all"]:
        return list(config.SUBURBS)
    out: list[dict[str, str]] = []
    for value in values:
        v = value.strip().lower()
        match = None
        for suburb in config.SUBURBS:
            if v in {suburb["slug"].lower(), suburb["name"].lower(), suburb["tm_name"].lower()}:
                match = suburb
                break
        if not match:
            raise SystemExit(f"Unknown suburb: {value!r}. Valid slugs: {', '.join(s['slug'] for s in config.SUBURBS)}")
        out.append(match)
    return out


def collect_search(
    client: TradeMeClient,
    suburbs: list[dict[str, str]],
    *,
    force: bool,
) -> tuple[dict[int, dict[str, Any]], list[dict[str, Any]]]:
    """Return {listing_id: basic} and per-suburb summary."""
    basics: dict[int, dict[str, Any]] = {}
    summaries: list[dict[str, Any]] = []
    for index, suburb in enumerate(suburbs, start=1):
        log.info("search %d/%d: %s", index, len(suburbs), suburb["name"])
        try:
            payload = client.search_suburb(suburb, force=force)
        except Exception as exc:  # keep going across suburbs
            log.error("search failed for %s: %s", suburb["name"], exc)
            client.log_error({"stage": "search", "suburb": suburb["slug"], "error": str(exc)})
            summaries.append({**suburb, "total_count": None, "collected": 0, "error": str(exc)})
            continue
        items = payload.get("items") or []
        for item in items:
            try:
                basic = parse_search_item(item, target_suburb=suburb)
            except Exception as exc:
                client.log_error(
                    {"stage": "parse_search", "suburb": suburb["slug"], "error": str(exc),
                     "listing_id": item.get("ListingId")}
                )
                continue
            if not basic.get("listing_id"):
                continue
            basics.setdefault(int(basic["listing_id"]), basic)
        summaries.append(
            {
                "name": suburb["name"],
                "slug": suburb["slug"],
                "canonical_path": payload.get("canonical_path"),
                "total_count": payload.get("total_count"),
                "collected": len(items),
                "unique_so_far": len(basics),
            }
        )
        log.info(
            "  %s: %s listings (API total %s)",
            suburb["name"], len(items), payload.get("total_count"),
        )
    return basics, summaries


def collect_one(
    client: TradeMeClient,
    basic: dict[str, Any],
    *,
    force: bool,
    fetch_schools: bool = True,
) -> dict[str, Any]:
    listing_id = int(basic["listing_id"])
    cached = client.cached_listing(listing_id)
    if not force:
        # A fallback record with no detail page must be retried on the next run.
        if cached and cached.get("detail_ok"):
            if fetch_schools and not cached.get("schools"):
                try:
                    cached["schools"] = parse_schools(
                        client.fetch_schools(listing_id)
                    )
                    client.save_listing(listing_id, cached)
                except Exception as exc:
                    client.log_error({"stage": "schools_cached", "listing_id": listing_id, "error": str(exc)[:500]})
            return cached

    captured_at = _iso_now()
    detail_state = None
    detail_error = None
    schools_payload = None

    canonical_path = basic.get("canonical_path") or ""
    if canonical_path:
        try:
            html = client.fetch_detail_html(canonical_path, listing_id)
            detail_state = parse_state(html)
        except Exception as exc:
            detail_error = str(exc)[:500]
            client.log_error(
                {"stage": "detail", "listing_id": listing_id, "url": basic.get("url"), "error": detail_error}
            )

    if fetch_schools:
        try:
            schools_payload = client.fetch_schools(listing_id)
        except Exception as exc:
            client.log_error({"stage": "schools", "listing_id": listing_id, "error": str(exc)[:500]})

    payload = merge_listing(
        basic,
        detail_state=detail_state,
        schools_payload=schools_payload,
        captured_at=captured_at,
    )
    if detail_error:
        payload["detail_error"] = detail_error
        payload["detail_ok"] = bool(detail_state)
    # A daily --force refresh must never destroy a previously good detail page when
    # only the detail fetch failed (e.g. Trade Me returns 406). Keep the cached AVM,
    # body, comps and school zones, while applying fresh search-level fields.
    if detail_state is None and cached and cached.get("detail_ok"):
        preserved = dict(cached)
        for key, value in basic.items():
            if value is not None:
                preserved[key] = value
        preserved["captured_at"] = captured_at
        preserved["detail_ok"] = True
        preserved["detail_error"] = detail_error
        preserved["detail_stale"] = True
        preserved["detail_cached_at"] = cached.get("captured_at")
        payload = preserved
    elif schools_payload is None and cached and cached.get("schools"):
        # Detail was refreshed but the school API failed; keep the zones we had.
        payload["schools"] = cached["schools"]
    client.save_listing(listing_id, payload)
    return payload


def run(args: argparse.Namespace) -> int:
    suburbs = resolve_suburbs(args.suburbs)
    client = TradeMeClient(spacing=args.spacing)
    started_at = _iso_now()
    log.info("target suburbs: %d", len(suburbs))

    basics, summaries = collect_search(client, suburbs, force=args.force_search)
    log.info("unique active listings: %d", len(basics))

    manifest: dict[str, Any] = {
        "started_at": started_at,
        "finished_at": None,
        "suburbs": summaries,
        "unique_listings": len(basics),
        "details_ok": 0,
        "details_missing_estimate": 0,
        "details_failed": 0,
        "only_search": args.only_search,
        "limit": args.limit,
    }

    if args.only_search:
        manifest["finished_at"] = _iso_now()
        path = config.RAW_DIR / "manifest.json"
        path.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
        print(json.dumps(manifest, indent=1))
        return 0

    if args.schools_only:
        files = sorted(config.LISTING_DIR.glob("*.json"))
        log.info("fetching school zones for %d cached listings", len(files))
        updated = 0
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            def task(path):
                data = json.loads(path.read_text(encoding="utf-8"))
                if data.get("schools"):
                    return False
                payload = client.fetch_schools(int(data["listing_id"]))
                data["schools"] = parse_schools(payload)
                client.save_listing(int(data["listing_id"]), data)
                return True
            for future in as_completed([executor.submit(task, p) for p in files]):
                try:
                    updated += 1 if future.result() else 0
                except Exception as exc:
                    log.warning("schools task failed: %s", exc)
        manifest["finished_at"] = _iso_now()
        manifest["schools_updated"] = updated
        (config.RAW_DIR / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
        print(json.dumps({"schools_updated": updated}, indent=1))
        return 0

    listing_ids = list(basics.keys())
    if args.limit:
        listing_ids = listing_ids[: args.limit]
    log.info("fetching details for %d listings", len(listing_ids))
    started = time.monotonic()
    done = 0
    failures = 0
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                collect_one, client, basics[lid], force=args.force,
                fetch_schools=not args.skip_schools,
            ): lid
            for lid in listing_ids
        }
        for future in as_completed(futures):
            listing_id = futures[future]
            done += 1
            try:
                payload = future.result()
            except Exception as exc:
                failures += 1
                log.error("listing %s failed: %s", listing_id, exc)
                client.log_error({"stage": "collect_one", "listing_id": listing_id, "error": str(exc)[:500]})
                continue
            if payload.get("detail_ok"):
                manifest["details_ok"] += 1
                if not (payload.get("homes") or {}).get("estimate_mid"):
                    manifest["details_missing_estimate"] += 1
            else:
                manifest["details_failed"] += 1
            if done % 25 == 0 or done == len(listing_ids):
                elapsed = time.monotonic() - started
                rate = done / elapsed if elapsed else 0
                remaining = (len(listing_ids) - done) / rate if rate else 0
                log.info(
                    "details %d/%d (%.1f/s, ~%.0f min left) ok=%d missing_avm=%d failed=%d",
                    done, len(listing_ids), rate, remaining / 60,
                    manifest["details_ok"], manifest["details_missing_estimate"],
                    manifest["details_failed"],
                )

    manifest["finished_at"] = _iso_now()
    manifest["failures"] = failures
    manifest_path = config.RAW_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    log.info("manifest written to %s", manifest_path)
    print(json.dumps(manifest, indent=1))
    return 0 if failures == 0 else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--suburbs", nargs="+", default=["all"], help="suburb slugs/names, or 'all'")
    p.add_argument("--limit", type=int, default=None, help="limit number of details (smoke test)")
    p.add_argument("--force", action="store_true", help="re-fetch cached detail pages")
    p.add_argument("--force-search", action="store_true", help="re-fetch cached search pages")
    p.add_argument("--only-search", action="store_true", help="only run the search inventory")
    p.add_argument("--skip-schools", action="store_true", help="skip the per-listing schools API")
    p.add_argument("--schools-only", action="store_true", help="fill missing school zones from cached listings")
    p.add_argument("--workers", type=int, default=config.MAX_WORKERS)
    p.add_argument("--spacing", type=float, default=config.REQUEST_SPACING_SECONDS)
    p.add_argument("--verbose", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
