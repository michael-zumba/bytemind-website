#!/usr/bin/env python3
"""Build the card that appears when somebody shares the ByteBook page.

The share card is the first thing most people see, and it goes stale in a way
nobody notices: it is a picture of the application, so every change to the
application makes it quietly wrong. The version it was built from, the number of
assurance procedures, the wording in the screenshot - all of it was a year old
within a month of being made.

So it is generated rather than drawn by hand. The card is a small HTML document
at exactly 1200x630, rendered with the site's own stylesheet and fonts, with the
dashboard screenshot beside it. Re-run this after a release and it cannot lag
behind.

    python3 scripts/make_bytebook_og.py            rebuild the card
    python3 scripts/make_bytebook_og.py --check    say whether it would change

Needs playwright with Chrome:

    pip install playwright
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets" / "bytebook"
OUT = ASSETS / "bytebook-og.png"
SHOT = ASSETS / "bytebook-dashboard.png"

WIDTH, HEIGHT = 1200, 630

# What the card says. Kept here, next to the layout, because the two are read
# together - a claim that no longer fits the space is a layout bug.
HEADLINE = "ByteBook"
LINES = (
    "Twelve practice businesses, already trading.",
    "Sixteen assurance procedures on the real rows.",
    "A handbook with every reference cited.",
)
FOOTER = "bytemind.co.nz/bytebook"


def html() -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<link rel="stylesheet" href="{ROOT / 'colors_and_type.css'}">
<style>
  @page {{ size: {WIDTH}px {HEIGHT}px; margin: 0; }}
  html, body {{ width: {WIDTH}px; height: {HEIGHT}px; margin: 0; overflow: hidden; }}
  body {{
    background: #f5f2e8;
    font-family: var(--font-serif);
    display: flex; align-items: center; gap: 48px;
    padding: 0 56px; box-sizing: border-box;
  }}
  .words {{ flex: 0 0 460px; }}
  h1 {{ font-size: 74px; line-height: 1; margin: 0 0 22px; color: #1a3a2a; letter-spacing: -0.02em; }}
  .rule {{ width: 118px; height: 3px; background: #c9a227; margin: 0 0 30px; }}
  p {{ font-family: var(--font-serif); font-size: 25px; line-height: 1.42; color: #2f332f; margin: 0 0 6px; }}
  .site {{ margin-top: 54px; font-family: var(--font-sans, sans-serif); font-size: 19px; color: #1a3a2a; }}
  .shot {{
    flex: 1; border-radius: 12px; overflow: hidden; background: #fff;
    border: 1px solid #dcd6c6; box-shadow: 0 24px 60px -30px rgba(14, 36, 25, .45);
    max-height: 500px;
  }}
  .shot img {{ display: block; width: 100%; height: auto; }}
</style>
</head>
<body>
  <div class="words">
    <h1>{HEADLINE}</h1>
    <div class="rule"></div>
    {"".join(f"<p>{line}</p>" for line in LINES)}
    <p class="site">{FOOTER}</p>
  </div>
  <div class="shot"><img src="{SHOT}" alt=""></div>
</body>
</html>
"""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def render(target: Path) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright is not installed: pip install playwright", file=sys.stderr)
        raise SystemExit(2)

    with tempfile.TemporaryDirectory(prefix="bytebook-og-") as work:
        page_file = Path(work) / "card.html"
        page_file.write_text(html(), encoding="utf-8")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="chrome")
            page = browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})
            page.goto(page_file.as_uri())
            # The dashboard screenshot is a local file and the fonts are remote,
            # so wait for both rather than racing them.
            page.wait_for_load_state("networkidle")
            page.screenshot(path=str(target))
            browser.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the ByteBook share card")
    parser.add_argument("--check", action="store_true",
                        help="rebuild into a temporary file and report whether it differs")
    args = parser.parse_args()

    for needed in (SHOT, ROOT / "colors_and_type.css"):
        if not needed.exists():
            print(f"missing {needed}", file=sys.stderr)
            return 1

    if args.check:
        with tempfile.TemporaryDirectory(prefix="bytebook-og-check-") as work:
            fresh = Path(work) / "card.png"
            render(fresh)
            print("the card is up to date" if digest(fresh) == digest(OUT)
                  else "the card is out of date - run without --check to rebuild it")
        return 0

    render(OUT)
    print(f"wrote {OUT.relative_to(ROOT)}  ({OUT.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
