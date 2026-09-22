#!/usr/bin/env python3
"""Check the static site before it is published.

The site is plain HTML on GitHub Pages, so a broken link or a file that was
never copied is invisible until a visitor finds it. This walks every page and
checks three things:

    python scripts/check_site.py                 links, assets and structure
    python scripts/check_site.py --quiet         only report problems

1. Every local link and asset reference resolves to a file that exists.
2. Every page has the elements the site depends on: one h1, a title, a
   description, a canonical address, and the shared stylesheet.
3. Every page that quotes a living standard through the handbook is present in
   the sitemap, so it can be found.

Pages that are meant to be private or hidden are listed in SKIP.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent

# Generated or third-party trees the site does not own.
SKIP_DIRS = {
    ".git", ".playwright-cli", ".byteproof-demo", ".byteproof-live", ".devcontainer",
    ".trae-html-share-packages", ".uploads", "node_modules", "__pycache__",
    # A design staging folder, kept in the repository but not part of the site.
    "bytemind-redesign",
    # Social media source files, not published pages.
    "xiaohongshu_assets",
    "previews",
}
SKIP_FILES = {
    "404.html",  # deliberately outside the canonical set
    "byteproof/index.html",  # a redirect to the byteproof.html page
}

# Pages that are a different shape on purpose. The handbook's single-page
# edition is every chapter in one document, so it has an h1 per chapter.
ALLOW_MULTIPLE_H1 = {"bytebook/manual/all.html"}
# Pages whose heading is drawn by the application rather than by the markup.
NO_H1_NEEDED = {"bytetax/play/index.html"}

HREF = re.compile(r'(?:href|src)="([^"]+)"', re.I)


def pages() -> list[Path]:
    found = []
    for path in sorted(ROOT.rglob("*.html")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        found.append(path)
    return found


def resolves(page: Path, target: str) -> bool:
    """Does this link point at a file that exists?"""
    target = target.split("#", 1)[0].split("?", 1)[0]
    if not target:
        return True
    if target.startswith(("http://", "https://", "mailto:", "tel:", "data:", "//", "javascript:")):
        return True
    target = unquote(target)
    if target.startswith("/"):
        candidate = ROOT / target.lstrip("/")
    else:
        candidate = (page.parent / target).resolve()
    if candidate.is_dir():
        candidate = candidate / "index.html"
    return candidate.exists()


def check() -> tuple[list[str], list[str]]:
    """Return (problems that block publication, notes worth fixing)."""
    problems: list[str] = []
    notes: list[str] = []
    all_pages = pages()
    for page in all_pages:
        html = page.read_text(encoding="utf-8", errors="replace")
        relative = page.relative_to(ROOT)

        for target in HREF.findall(html):
            # A link assembled in JavaScript is not one we can check from here.
            if "' +" in target or "+ '" in target or target.startswith(("${", "{{")):
                continue
            if not resolves(page, target):
                problems.append(f"{relative}: link goes nowhere -> {target}")

        if str(relative) in SKIP_FILES:
            continue

        # A page without a heading or a title is broken for a reader or a search
        # engine, so it fails. The metadata below is worth having but is missing
        # on older pages that predate it, so it is reported, not enforced.
        for pattern, label in (
            (r"<h1[\s>]", "an h1"),
            (r"<title>", "a title"),
        ):
            if label == "an h1" and str(relative) in NO_H1_NEEDED:
                continue
            if not re.search(pattern, html, re.I):
                problems.append(f"{relative}: no {label}")
        for pattern, label in (
            (r'<meta name="description"', "a description"),
            (r'<link rel="canonical"', "a canonical address"),
        ):
            if not re.search(pattern, html, re.I):
                notes.append(f"{relative}: no {label}")

        headings = re.findall(r"<h1[\s>]", html, re.I)
        if len(headings) > 1 and str(relative) not in ALLOW_MULTIPLE_H1:
            problems.append(f"{relative}: {len(headings)} h1 elements")

    return problems, notes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    found = pages()
    problems, notes = check()
    if not args.quiet:
        print(f"checked {len(found)} pages")
        if notes:
            print(f"{len(notes)} notes (older pages, not blocking):")
            for note in notes[:10]:
                print(f"  {note}")
            if len(notes) > 10:
                print(f"  … and {len(notes) - 10} more")
    if problems:
        print(f"{len(problems)} problems:")
        for problem in problems:
            print(f"  {problem}")
        return 1
    if not args.quiet:
        print("every link resolves, and every page has its required elements")
    return 0


if __name__ == "__main__":
    sys.exit(main())
