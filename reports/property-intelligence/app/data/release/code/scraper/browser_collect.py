"""Browser-based fallback collector for listing detail pages.

Trade Me's anti-bot layer sometimes returns 406 to curl after a few hundred pages,
while a real browser session still receives the server-rendered `frend-state` blob.
This script uses Playwright, blocks images/scripts/fonts/styles, and parses the
initial HTML before Angular has a chance to run. It is deliberately slower and
used only for pages the normal collector could not fetch.

Usage::

    python -m scraper.browser_collect
    python -m scraper.browser_collect --workers 2 --limit 20
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright

from . import config
from .parse import merge_listing, parse_search_item, parse_state

log = logging.getLogger("scraper.browser_collect")

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
BLOCKED_TYPES = {"image", "font", "stylesheet", "media", "script"}


def load_catalogue() -> dict[int, dict[str, Any]]:
    """All active listings from cached search responses, keyed by listing id."""
    by_slug = {s["slug"]: s for s in config.SUBURBS}
    catalogue: dict[int, dict[str, Any]] = {}
    for path in sorted((config.RAW_DIR / "search").glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        suburb = by_slug.get(payload.get("slug"))
        if not suburb:
            continue
        for item in payload.get("items") or []:
            listing_id = item.get("ListingId")
            if listing_id and int(listing_id) not in catalogue:
                catalogue[int(listing_id)] = {
                    "item": item,
                    "suburb": suburb,
                }
    return catalogue


def load_existing() -> dict[int, dict[str, Any]]:
    existing: dict[int, dict[str, Any]] = {}
    for path in (config.RAW_DIR / "listings").glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if data.get("listing_id"):
            existing[int(data["listing_id"])] = data
    return existing


def needs_detail(data: dict[str, Any] | None) -> bool:
    return not data or not data.get("detail_ok")


def save_listing(data: dict[str, Any]) -> None:
    listing_id = int(data["listing_id"])
    path = config.LISTING_DIR / f"{listing_id}.json"
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)


def fallback(basic: dict[str, Any], error: str, captured_at: str) -> dict[str, Any]:
    payload = merge_listing(basic, captured_at=captured_at)
    payload["detail_ok"] = False
    payload["detail_error"] = error[:500]
    return payload


async def fetch_one(page, url: str) -> str | None:
    for attempt in range(2):
        try:
            resp = await page.goto(url, wait_until="domcontentloaded", timeout=35_000)
            if resp and resp.status == 200:
                html = await page.content()
                if 'id="frend-state"' in html:
                    return html
        except Exception as exc:  # noqa: BLE001 - browser errors are varied
            log.debug("browser fetch failed (%s): %s", attempt, exc)
        await asyncio.sleep(2.0 + random.random())
    return None


class Pacer:
    def __init__(self, spacing: float):
        self.spacing = spacing
        self._lock = asyncio.Lock()
        self._next = 0.0

    async def wait(self) -> None:
        async with self._lock:
            now = time.monotonic()
            delay = max(0.0, self._next - now)
            self._next = max(now, self._next) + self.spacing
        if delay:
            await asyncio.sleep(delay)


async def worker(
    name: str,
    browser,
    queue: asyncio.Queue,
    catalogue: dict[int, dict[str, Any]],
    existing: dict[int, dict[str, Any]],
    pacer: Pacer,
    progress: dict[str, int],
    total: int,
) -> None:
    context = await browser.new_context(user_agent=USER_AGENT, locale="en-NZ")
    await context.route(
        "**/*",
        lambda route: route.abort()
        if route.request.resource_type in BLOCKED_TYPES
        else route.continue_(),
    )
    page = await context.new_page()
    while True:
        try:
            listing_id = queue.get_nowait()
        except asyncio.QueueEmpty:
            break
        entry = catalogue[listing_id]
        basic = parse_search_item(entry["item"], target_suburb=entry["suburb"])
        url = basic.get("url")
        if not url:
            queue.task_done()
            continue
        await pacer.wait()
        html = await fetch_one(page, url)
        captured_at = datetime.now(timezone.utc).isoformat()
        if html:
            try:
                state = parse_state(html)
                payload = merge_listing(basic, detail_state=state, captured_at=captured_at)
            except Exception as exc:  # noqa: BLE001
                payload = fallback(basic, f"parse error: {exc}", captured_at)
        else:
            payload = fallback(basic, "browser fetch failed", captured_at)
        save_listing(payload)
        progress["done"] += 1
        progress["ok"] += 1 if payload.get("detail_ok") else 0
        if progress["done"] % 25 == 0 or progress["done"] == total:
            log.info(
                "%s: %d/%d (ok=%d failed=%d)", name, progress["done"], total,
                progress["ok"], progress["done"] - progress["ok"],
            )
        queue.task_done()


async def run(args: argparse.Namespace) -> int:
    catalogue = load_catalogue()
    existing = load_existing()
    pending = [lid for lid in catalogue if needs_detail(existing.get(lid))]
    if args.limit:
        pending = pending[: args.limit]
    log.info(
        "catalogue=%d existing=%d pending=%d", len(catalogue), len(existing), len(pending)
    )
    if not pending:
        return 0

    queue: asyncio.Queue = asyncio.Queue()
    for lid in pending:
        queue.put_nowait(lid)
    progress = {"done": 0, "ok": 0}
    pacer = Pacer(args.spacing)

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        try:
            await asyncio.gather(
                *[
                    worker(
                        f"w{i+1}", browser, queue, catalogue, existing, pacer, progress,
                        len(pending),
                    )
                    for i in range(max(1, args.workers))
                ]
            )
        finally:
            await browser.close()
    print(json.dumps({"pending": len(pending), **progress}, indent=1))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--spacing", type=float, default=0.9)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    return asyncio.run(run(args))


if __name__ == "__main__":
    sys.exit(main())
