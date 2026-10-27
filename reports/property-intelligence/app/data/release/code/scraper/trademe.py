"""HTTP client for the public Trade Me property pages/APIs.

Trade Me's public site is an Angular app. Server-rendered pages contain a large
`frend-state` JSON blob with the useful data; its own front-end APIs are public but
require browser-like Referer/Origin headers.
"""
from __future__ import annotations

import json
import random
import shutil
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from . import config


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None = None) -> str:
    return (dt or utc_now()).isoformat()


class TradeMeError(RuntimeError):
    pass


class RateLimiter:
    """Process-wide spacing between outbound requests, safe across threads."""

    def __init__(self, spacing: float):
        self.spacing = max(0.05, spacing)
        self._lock = threading.Lock()
        self._next_at = 0.0

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            delay = max(0.0, self._next_at - now)
            self._next_at = max(now, self._next_at) + self.spacing
        if delay:
            time.sleep(delay)


class TradeMeClient:
    def __init__(
        self,
        raw_dir: Path | None = None,
        spacing: float | None = None,
        timeout: int = config.REQUEST_TIMEOUT,
        retries: int = config.MAX_RETRIES,
    ):
        self.raw_dir = Path(raw_dir or config.RAW_DIR)
        self.search_dir = self.raw_dir / "search"
        self.listing_dir = self.raw_dir / "listings"
        self.search_dir.mkdir(parents=True, exist_ok=True)
        self.listing_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.retries = retries
        self.limiter = RateLimiter(spacing if spacing is not None else config.REQUEST_SPACING_SECONDS)
        self._local = threading.local()
        self._error_lock = threading.Lock()
        self.errors_path = self.raw_dir / "errors.jsonl"

    # ------------------------------------------------------------------ HTTP
    @property
    def session(self) -> requests.Session:
        session = getattr(self._local, "session", None)
        if session is None:
            session = requests.Session()
            session.headers.update({"Connection": "keep-alive"})
            self._local.session = session
        return session

    def _request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, Any] | None = None,
    ) -> requests.Response:
        last_error: Exception | None = None
        for attempt in range(1, self.retries + 1):
            self.limiter.wait()
            try:
                resp = self.session.request(
                    method, url, headers=headers, params=params, timeout=self.timeout
                )
            except requests.RequestException as exc:  # network error
                last_error = exc
            else:
                if resp.status_code == 200:
                    return resp
                if resp.status_code in (406, 429) or resp.status_code >= 500:
                    # 406 is Trade Me's anti-bot/rate-limit response. Back off hard
                    # rather than hammering the endpoint.
                    last_error = TradeMeError(f"HTTP {resp.status_code} for {url}")
                    retry_after = resp.headers.get("Retry-After")
                    try:
                        retry_after_s = float(retry_after) if retry_after else 0
                    except ValueError:
                        retry_after_s = 0
                    sleep_for = max(30.0, retry_after_s) if resp.status_code == 406 else min(60.0, (2 ** (attempt - 1)) + random.random())
                    time.sleep(sleep_for)
                    continue
                else:
                    raise TradeMeError(
                        f"HTTP {resp.status_code} for {url}: {resp.text[:300]}"
                    )
            sleep_for = min(30.0, (2 ** (attempt - 1)) + random.random())
            time.sleep(sleep_for)
        raise TradeMeError(f"request failed after {self.retries} attempts: {url} ({last_error})")

    # curl has a browser-like TLS fingerprint; Python's urllib3 can receive
    # Akamai 406 responses after a modest number of HTML requests.
    def _curl_get(self, url: str, headers: dict[str, str], timeout: int | None = None) -> tuple[int, str]:
        curl = shutil.which("curl")
        if not curl:
            raise TradeMeError("curl is required for HTML detail fetching")
        cmd = [curl, "-sS", "--compressed", "--max-time", str(timeout or self.timeout)]
        for key, value in headers.items():
            cmd += ["-H", f"{key}: {value}"]
        cmd += ["-w", "\n__APR_STATUS__:%{http_code}", url]
        result = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
        out = result.stdout
        if "__APR_STATUS__:" not in out:
            raise TradeMeError(f"curl failed: {result.stderr[:300]}")
        body, status_text = out.rsplit("\n__APR_STATUS__:", 1)
        try:
            status = int(status_text.strip())
        except ValueError:
            status = 0
        return status, body

    def log_error(self, record: dict[str, Any]) -> None:
        record = {"logged_at": _iso(), **record}
        with self._error_lock:
            with self.errors_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    # ------------------------------------------------------------------ Search
    def search_suburb(self, suburb: dict[str, str], *, force: bool = False) -> dict[str, Any]:
        slug = suburb["slug"]
        cache_path = self.search_dir / f"{slug}.json"
        if not force and cache_path.exists():
            age_hours = (utc_now().timestamp() - cache_path.stat().st_mtime) / 3600
            if age_hours <= config.SEARCH_CACHE_HOURS:
                with cache_path.open(encoding="utf-8") as fh:
                    cached = json.load(fh)
                if cached.get("items"):
                    return cached

        canonical_path = (
            f"/property/residential/sale/auckland/{suburb['district']}/{suburb['slug']}"
        )
        items: list[dict[str, Any]] = []
        pages = 0
        total_count: int | None = None
        page = 1
        while page <= 20:
            params = {
                "page": page,
                "rows": 200,
                "canonical_path": canonical_path,
                "return_canonical": "true",
                "return_metadata": "true",
                "return_ads": "true",
                "return_empty_categories": "true",
                "return_super_features": "true",
                "return_did_you_mean": "true",
                "return_variants": "true",
            }
            resp = self._request(
                "GET", f"{config.API_BASE}/search/property/residential.json",
                headers=config.JSON_HEADERS, params=params,
            )
            payload = resp.json()
            pages += 1
            total_count = int(payload.get("TotalCount") or 0)
            batch = payload.get("List") or []
            items.extend(batch)
            if not batch or len(items) >= total_count:
                break
            page += 1

        # De-duplicate while preserving order; API can return the same premium listing twice.
        seen: set[int] = set()
        unique: list[dict[str, Any]] = []
        for item in items:
            listing_id = item.get("ListingId")
            if listing_id and listing_id not in seen:
                seen.add(listing_id)
                unique.append(item)

        result = {
            "captured_at": _iso(),
            "suburb": suburb["name"],
            "tm_name": suburb["tm_name"],
            "slug": slug,
            "district": suburb["district"],
            "canonical_path": canonical_path,
            "total_count": total_count if total_count is not None else len(unique),
            "page_size": len(unique),
            "pages_fetched": pages,
            "items": unique,
        }
        with cache_path.open("w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=1)
        return result

    # ------------------------------------------------------------------ Detail
    def fetch_detail_html(self, canonical_path: str, listing_id: int) -> str:
        url = f"{config.WEB_BASE}/a{canonical_path}"
        headers = dict(config.HTML_HEADERS)
        headers["Referer"] = f"{config.WEB_BASE}/"
        last_error: Exception | None = None
        for attempt in range(1, 3):
            self.limiter.wait()
            try:
                status, html = self._curl_get(url, headers)
            except Exception as exc:
                last_error = exc
                status, html = 0, ""
            if status == 200 and 'id="frend-state"' in html:
                return html
            last_error = TradeMeError(f"HTTP {status}; frend-state={'frend-state' in html}")
            if status in (406, 429):
                # Fail fast rather than burning minutes on a rate-limit loop; the
                # listing is saved as a fallback and retried on the next pass.
                time.sleep(8.0 + random.random() * 3)
            elif status >= 500 or status == 0:
                time.sleep(3 ** attempt + random.random())
            else:
                time.sleep(1.5 * attempt + random.random())
        raise TradeMeError(f"detail page unparsable after retries: {listing_id} ({last_error})")

    def fetch_listing_basic(self, listing_id: int) -> dict[str, Any]:
        resp = self._request(
            "GET", f"{config.API_BASE}/listings/{listing_id}.json",
            headers=config.JSON_HEADERS,
        )
        return resp.json()

    def fetch_schools(self, listing_id: int) -> dict[str, Any]:
        url = f"{config.API_BASE}/listings/{listing_id}/schools.json"
        # Prefer curl's browser-like TLS fingerprint; the JSON API is normally
        # friendlier than the HTML pages but can still be rate-limited.
        try:
            status, body = self._curl_get(url, config.JSON_HEADERS, timeout=30)
            if status == 200 and body.strip():
                return json.loads(body)
        except (TradeMeError, json.JSONDecodeError):
            pass
        resp = self._request("GET", url, headers=config.JSON_HEADERS)
        return resp.json()

    # ------------------------------------------------------------------ Cache helpers
    def cached_listing(self, listing_id: int, max_age_hours: float = config.LISTING_CACHE_HOURS) -> dict[str, Any] | None:
        path = self.listing_dir / f"{listing_id}.json"
        if not path.exists():
            archived = self.listing_dir / f"{listing_id}.json.gz"
            path = archived if archived.exists() else path
        if not path.exists():
            return None
        age_hours = (utc_now().timestamp() - path.stat().st_mtime) / 3600
        if age_hours > max_age_hours:
            return None
        try:
            if path.name.endswith(".gz"):
                with gzip.open(path, "rt", encoding="utf-8") as fh:
                    data = json.load(fh)
            else:
                with path.open(encoding="utf-8") as fh:
                    data = json.load(fh)
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(data, dict) or not data.get("listing_id"):
            return None
        return data

    def save_listing(self, listing_id: int, payload: dict[str, Any]) -> Path:
        path = self.listing_dir / f"{listing_id}.json"
        archived = self.listing_dir / f"{listing_id}.json.gz"
        if archived.exists():
            try:
                archived.unlink()
            except OSError:
                pass
        tmp = path.with_suffix(".json.tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=1)
        tmp.replace(path)
        return path
