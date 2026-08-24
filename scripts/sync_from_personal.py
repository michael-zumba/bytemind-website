#!/usr/bin/env python3
"""Sync research briefs (reports) from the personal website to the ByteMind website.

Auto-detects new or updated reports under:
    <personal>/public/reports/<slug>/
and publishes them to:
    <bytemind>/reports/<slug>/
in the ByteMind format:

  1. charts/, data/, scripts/ and summary.html are copied as-is.
  2. index.html is converted to the ByteMind template:
       - ByteMind design CSS + self-hosted fonts/echarts
       - local chart-download utility (kept from the personal site)
       - a Key Terms callout (from reports/.sync-meta.json)
       - Back to Reports / Back to Insights footer navigation
  3. reports/manifest.json is updated (Reports page).
  4. A summary post is generated from the executive summary and registered in
     posts/manifest.json (Insights page).
  5. Research-indicator panels, metric tiles and "Read the full reports" cards
     are added to indices.html + assets/js/indices.js from
     reports/.sync-indices.json.
  6. sitemap.xml gains the new report URL.

State is tracked in reports/.sync-state.json (per-report fingerprint), so
unmodified reports are skipped on subsequent runs.

Usage:
    python3 scripts/sync_from_personal.py [--dry-run]

Optional env overrides:
    BYTEMIND_ROOT, PERSONAL_WEBSITE_ROOT
"""

import datetime as _dt
import hashlib
import html as _html
import json
import os
import re
import shutil
import sys


BYTEMIND_ROOT = os.environ.get(
    "BYTEMIND_ROOT",
    "/Users/zhangy6j/Python Projects/Personal/ByteMind Project/ByteMind_Website",
)
PERSONAL_ROOT = os.environ.get(
    "PERSONAL_WEBSITE_ROOT",
    "/Users/zhangy6j/Python Projects/Personal/Personal website",
)

SRC_REPORTS = os.path.join(PERSONAL_ROOT, "public", "reports")
DST_REPORTS = os.path.join(BYTEMIND_ROOT, "reports")
DST_POSTS = os.path.join(BYTEMIND_ROOT, "posts")

STATE_PATH = os.path.join(DST_REPORTS, ".sync-state.json")
META_PATH = os.path.join(DST_REPORTS, ".sync-meta.json")
INDICES_SPEC_PATH = os.path.join(DST_REPORTS, ".sync-indices.json")

TEMPLATE_HTML = os.path.join(DST_REPORTS, "ai-digital-transformation", "index.html")
SHARED_SOURCE = os.path.join(DST_REPORTS, "property-market-analysis", "_shared")

CHART_DOWNLOAD_JS = os.path.join(SRC_REPORTS, "chart-download.js")
CHART_DOWNLOAD_CSS = os.path.join(SRC_REPORTS, "chart-download.css")

INDICES_HTML = os.path.join(BYTEMIND_ROOT, "indices.html")
INDICES_JS = os.path.join(BYTEMIND_ROOT, "assets", "js", "indices.js")
SITEMAP_XML = os.path.join(BYTEMIND_ROOT, "sitemap.xml")

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12,
}


def log(msg):
    print(msg)


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data, indent=2):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
        f.write("\n")


def strip_tags(text):
    text = re.sub(r"<[^>]+>", "", text)
    return _html.unescape(text).strip()


def slug_dir_fingerprint(slug_dir):
    h = hashlib.sha256()
    for root, dirs, files in os.walk(slug_dir):
        dirs[:] = [d for d in dirs if d not in (".DS_Store", ".git")]
        for fname in sorted(files):
            if fname == ".DS_Store":
                continue
            path = os.path.join(root, fname)
            rel = os.path.relpath(path, slug_dir)
            st = os.stat(path)
            h.update(rel.encode("utf-8"))
            h.update(str(st.st_size).encode("utf-8"))
            h.update(str(int(st.st_mtime)).encode("utf-8"))
    return h.hexdigest()


def discover_reports():
    found = {}
    if not os.path.isdir(SRC_REPORTS):
        return found
    for slug in sorted(os.listdir(SRC_REPORTS)):
        subdir = os.path.join(SRC_REPORTS, slug)
        if not os.path.isdir(subdir) or slug.startswith("."):
            continue
        if os.path.exists(os.path.join(subdir, "index.html")):
            found[slug] = subdir
    return found


def copy_tree(src, dst, skip_names=()):
    if not os.path.isdir(src):
        return
    os.makedirs(dst, exist_ok=True)
    for name in os.listdir(src):
        if name in skip_names:
            continue
        s = os.path.join(src, name)
        d = os.path.join(dst, name)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)


def extract_css(template_html_path):
    with open(template_html_path, "r", encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"<style>(.*?)</style>", text, re.S)
    if not m:
        raise RuntimeError("Could not extract ByteMind CSS from %s" % template_html_path)
    return m.group(1).strip()


def normalize_meta(text):
    text = strip_tags(text)
    author = text.split("|")[0].split(",")[0].strip()
    if not author:
        author = "Dr Yuqian Zhang"
    m = re.search(r"(\d{1,2}\s+[A-Za-z]+\s+\d{4})", text)
    date = m.group(1) if m else ""
    parts = [author]
    if date:
        parts.append(date)
    parts.append("Analytical Brief")
    return " &middot; ".join(parts)


def meta_date_to_iso(text):
    m = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", text)
    if not m:
        return ""
    day, month, year = m.group(1), m.group(2).lower(), m.group(3)
    if month not in MONTHS:
        return ""
    return "%04d-%02d-%02d" % (int(year), MONTHS[month], int(day))


def build_key_terms_html(terms):
    if not terms:
        return ""
    items = "".join(
        "<p><strong>%s</strong> \u2014 %s</p>" % (_html.escape(t["term"]), _html.escape(t["def"]))
        for t in terms
    )
    return (
        '<div class="callout" id="key-terms">\n'
        "  <h4>Key Terms</h4>\n"
        "%s\n"
        "</div>\n"
    ) % items


def extract_exec_first_para(content):
    m = re.search(r'<section class="exec-summary">(.*?)</section>', content, re.S)
    if not m:
        return ""
    p = re.search(r"<p>(.*?)</p>", m.group(1), re.S)
    return strip_tags(p.group(1)) if p else ""


def extract_key_findings(content):
    m = re.search(r'<ul class="key-findings">(.*?)</ul>', content, re.S)
    if not m:
        return []
    items = re.findall(r"<li>(.*?)</li>", m.group(1), re.S)
    return [strip_tags(x) for x in items if strip_tags(x)]


def extract_toc(content):
    m = re.search(
        r'<(?:section|nav) class="toc">(.*?)</(?:section|nav)>', content, re.S
    )
    if not m:
        return []
    items = re.findall(r'<li><a href="[^"]*">(.*?)</a></li>', m.group(1), re.S)
    return [strip_tags(x) for x in items if strip_tags(x)]


def convert_index(src_path, dst_path, slug, meta, css):
    with open(src_path, "r", encoding="utf-8") as f:
        html = f.read()

    title_m = re.search(r"<title>(.*?)</title>", html, re.S)
    title = strip_tags(title_m.group(1)) if title_m else slug.replace("-", " ").title()

    body_m = re.search(r"<body[^>]*>(.*?)<script", html, re.S)
    if not body_m:
        raise RuntimeError("Could not locate <body> content in %s" % src_path)
    content = body_m.group(1)

    # --- Normalise ByteMind chrome -------------------------------------------------
    content = content.replace("<header>", '<header class="cover">', 1)
    content = re.sub(
        r'<div class="subtitle">(.*?)</div>',
        lambda m: '<p class="subtitle">%s</p>' % m.group(1),
        content,
        count=1,
        flags=re.S,
    )
    content = re.sub(
        r'<div class="meta">(.*?)</div>',
        lambda m: '<p class="meta">%s</p>' % normalize_meta(m.group(1)),
        content,
        count=1,
        flags=re.S,
    )
    # internal absolute links -> relative links that work inside reports/<slug>/
    content = re.sub(r'href="/%s/' % re.escape(slug), 'href="', content)
    content = content.replace('href="/"', 'href="../../reports.html"')

    # --- Key Terms callout after the executive summary ----------------------------
    key_terms_html = build_key_terms_html(meta.get("key_terms", []))
    if key_terms_html:
        m = re.search(r'<section class="exec-summary">.*?</section>', content, re.S)
        if m:
            content = content[: m.end()] + "\n" + key_terms_html + content[m.end() :]

    # --- Chart configuration block ------------------------------------------------
    chart_js = ""
    m = re.search(
        r"<script>(.*?)</script>\s*<script src=\"\.\./chart-download\.js\"",
        html,
        re.S,
    )
    if m:
        chart_js = m.group(1).strip()
    else:
        blocks = re.findall(r"<script>(.*?)</script>", html, re.S)
        if blocks:
            chart_js = blocks[-1].strip()

    out = (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8"/>\n'
        '<meta content="width=device-width, initial-scale=1.0" name="viewport"/>\n'
        '<link href="../../assets/bytemind-logo.png?v=2026" rel="icon"/>\n'
        '<link rel="stylesheet" href="../chart-download.css"/>\n'
        "<title>%s</title>\n"
        "<style>\n%s\n</style>\n"
        "</head>\n"
        "<body>\n"
        '<div class="container">\n'
        "%s\n"
        '<div class="footer-nav">\n'
        '<a href="../../reports.html">Back to Reports</a>\n'
        '<a href="../../insights.html">Back to Insights</a>\n'
        "</div>\n"
        "</div>\n"
        '<script src="./_shared/js/echarts.min.js"></script>\n'
        "<script>\n"
        'window.__bmPalette = (function(){var s=getComputedStyle(document.documentElement);'
        'return {accent:s.getPropertyValue("--accent").trim(),'
        'gold:s.getPropertyValue("--accent2").trim(),'
        'muted:s.getPropertyValue("--muted").trim(),'
        'rule:s.getPropertyValue("--rule").trim(),'
        'ink:s.getPropertyValue("--ink").trim(),'
        'bg2:s.getPropertyValue("--bg2").trim(),'
        'teal:"#3d6b5b",green:"#2f6b4f",red:"#a33b2f"};})();\n'
        "</script>\n"
        "<script>\n%s\n</script>\n"
        '<script src="../chart-download.js"></script>\n'
        "</body>\n"
        "</html>\n"
    ) % (title, css, content, chart_js)

    with open(dst_path, "w", encoding="utf-8") as f:
        f.write(out)
    return title


def upsert_manifest(manifest_path, entry, key="filename"):
    manifest = load_json(manifest_path, [])
    for i, item in enumerate(manifest):
        if item.get(key) == entry.get(key):
            manifest[i] = entry
            break
    else:
        manifest.append(entry)
    save_json(manifest_path, manifest, indent=4)


def generate_post(slug, meta, content, dst_posts):
    date = meta.get("date", "")
    title = meta.get("post_title") or meta.get("title", slug)
    summary = meta.get("post_summary") or meta.get("summary", "")
    intro = extract_exec_first_para(content)
    findings = extract_key_findings(content)
    toc = extract_toc(content)

    lines = [
        "---",
        'title: "%s"' % title.replace('"', '\\"'),
        "date: %s" % date,
        'summary: "%s"' % summary.replace('"', '\\"'),
        "---",
        "",
    ]
    if intro:
        lines += [intro, ""]
    if findings:
        lines += ["## Key findings", ""]
        lines += ["- %s" % f for f in findings]
        lines += [""]
    if toc:
        lines += ["## What the report covers", ""]
        lines += ["- %s" % t for t in toc]
        lines += [""]
    lines += ["[Read the full analytical brief](/reports/%s/)" % slug, ""]

    filename = "%s-%s.md" % (date, slug)
    with open(os.path.join(dst_posts, filename), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return filename


def js_str_array(values):
    return "[" + ", ".join('"%s"' % str(v).replace('"', '\\"') for v in values) + "]"


def js_num_array(values):
    return "[" + ", ".join(str(v) for v in values) + "]"


def js_row_array(rows):
    return (
        "["
        + ", ".join(js_str_array(row) for row in rows)
        + "]"
    )


def generate_indices_js(panel):
    var = "v_" + re.sub(r"[^A-Za-z0-9]", "_", panel["chartId"])
    labels = panel["labels"]
    values = panel["values"]
    series_name = panel.get("seriesName", "Value")
    unit = panel.get("unit", "")
    chart_id = panel["chartId"]
    table_id = panel["tableId"]
    columns = panel["tableColumns"]
    rows = panel["tableRows"]
    return (
        "\n    // ==== SYNC: %s ====\n"
        "    var %s_years = %s;\n"
        "    var %s_values = %s;\n"
        "    setOption('%s', {\n"
        "        tooltip: lineTooltip(),\n"
        "        legend: { data: ['%s'], top: 0, textStyle: { color: muted } },\n"
        "        grid: { left: 56, right: 24, top: 44, bottom: 40 },\n"
        "        xAxis: catAxis(%s_years),\n"
        "        yAxis: valAxis('%s'),\n"
        "        color: [accent2],\n"
        "        series: [{ name: '%s', type: 'line', data: %s_values, smooth: true, "
        "lineStyle: { width: 2.5 }, symbol: 'circle', symbolSize: 5 }]\n"
        "    });\n"
        "    renderTable('%s', %s, %s);\n"
    ) % (
        panel.get("_slug", ""),
        var, js_str_array(labels),
        var, js_num_array(values),
        chart_id, series_name.replace("'", "\\'"),
        var, unit.replace("'", "\\'"),
        series_name.replace("'", "\\'"), var,
        table_id, js_str_array(columns), js_row_array(rows),
    )


def apply_indices(slug, spec):
    """Insert metric tiles, indicator panels, cards, and chart JS (idempotent)."""
    changed = []

    with open(INDICES_HTML, "r", encoding="utf-8") as f:
        page = f.read()

    metric_marker = "<!-- SYNC-METRIC:%s -->" % slug
    if spec.get("metrics") and metric_marker not in page:
        tiles = "".join(
            (
                '        <div class="metric-item">\n'
                '          <div class="metric-value">%s</div>\n'
                '          <span class="metric-label">%s</span>\n'
                "        </div>\n"
            )
            % (_html.escape(m["value"]), _html.escape(m["label"]))
            for m in spec["metrics"]
        )
        block = "%s\n%s" % (metric_marker, tiles)
        m = re.search(r'<section class="metric-strip"[^>]*>(.*?)</section>', page, re.S)
        if m:
            page = page[: m.end() - len("</section>")] + block + "</section>" + page[m.end():]
            changed.append("indices.html metrics")

    panel_marker = "<!-- SYNC-PANEL:%s -->" % slug
    if spec.get("panels") and panel_marker not in page:
        panels_html = []
        for panel in spec["panels"]:
            accordion_id = "accordion-" + panel["tableId"]
            panels_html.append(
                (
                    '      <h3 class="chart-heading chart-heading--spaced">%s</h3>\n'
                    "      <p class=\"caption\">%s</p>\n"
                    '      <div id="%s" class="chart-box chart-md" role="img" aria-label="%s"></div>\n'
                    "      <div class=\"accordion\">\n"
                    '        <button type="button" class="accordion-header" aria-expanded="false" '
                    'aria-controls="%s">\n'
                    '          <span class="accordion-title accordion-title--sm">View Data Table</span>\n'
                    '          <span class="accordion-icon">&#9660;</span>\n'
                    "        </button>\n"
                    '        <div id="%s" class="accordion-content">\n'
                    '          <div id="%s" class="data-table-wrap"></div>\n'
                    '          <a href="%s" download class="btn btn-secondary btn-sm csv-link">'
                    "Download CSV</a>\n"
                    "        </div>\n"
                    "      </div>\n"
                )
                % (
                    _html.escape(panel["heading"]),
                    _html.escape(panel["caption"]),
                    panel["chartId"],
                    _html.escape(panel.get("aria", "")),
                    accordion_id,
                    accordion_id,
                    panel["tableId"],
                    panel["csvPath"],
                )
            )
        block = "%s\n%s" % (panel_marker, "".join(panels_html))
        anchor = "        <!-- Related Research -->"
        idx = page.find(anchor)
        if idx != -1:
            before = page[:idx]
            close = before.rfind("</div>")
            if close != -1:
                page = page[:close] + block + "\n" + page[close:]
                changed.append("indices.html panels")

    card_marker = "<!-- SYNC-CARD:%s -->" % slug
    card = spec.get("card")
    if card and card_marker not in page:
        block = (
            "%s\n"
            "            <div class=\"card\">\n"
            "              <h4>%s</h4>\n"
            "              <p>%s</p>\n"
            '              <a href="%s" class="inline-link">Read the report &rarr;</a>\n'
            "            </div>\n"
        ) % (
            card_marker,
            _html.escape(card["title"]),
            _html.escape(card["desc"]),
            card["link"],
        )
        anchor = '          <div class="section-link-row"'
        idx = page.find(anchor)
        if idx != -1:
            before = page[:idx]
            close = before.rfind("</div>")
            if close != -1:
                page = page[:close] + block + page[close:]
                changed.append("indices.html card")

    if spec.get("sources_note"):
        page = re.sub(
            r'<p class="metric-note">.*?</p>',
            '<p class="metric-note">%s</p>' % _html.escape(spec["sources_note"]),
            page,
            count=1,
            flags=re.S,
        )
        changed.append("indices.html metric note")

    with open(INDICES_HTML, "w", encoding="utf-8") as f:
        f.write(page)

    # --- indices.js ---------------------------------------------------------------
    with open(INDICES_JS, "r", encoding="utf-8") as f:
        js = f.read()
    for panel in spec.get("panels", []):
        panel = dict(panel, _slug=slug)
        marker = "// ==== SYNC: %s ====" % slug
        if marker in js:
            continue
        js_block = generate_indices_js(panel)
        close = js.rfind("\n});")
        if close == -1:
            continue
        js = js[: close + 1] + js_block + js[close + 1:]
        changed.append("indices.js charts")
    with open(INDICES_JS, "w", encoding="utf-8") as f:
        f.write(js)

    # --- sitemap ------------------------------------------------------------------
    with open(SITEMAP_XML, "r", encoding="utf-8") as f:
        sitemap = f.read()
    url = "https://www.bytemind.co.nz/reports/%s/" % slug
    if url not in sitemap:
        entry = (
            "    <url>\n"
            "        <loc>%s</loc>\n"
            "        <changefreq>monthly</changefreq>\n"
            "        <priority>0.7</priority>\n"
            "    </url>\n"
        ) % url
        sitemap = sitemap.replace("</urlset>", entry + "</urlset>")
        with open(SITEMAP_XML, "w", encoding="utf-8") as f:
            f.write(sitemap)
        changed.append("sitemap.xml")

    return changed


def main():
    dry_run = "--dry-run" in sys.argv
    reports = discover_reports()
    if not reports:
        log("No reports discovered under %s" % SRC_REPORTS)
        return 1

    state = load_json(STATE_PATH, {})
    meta_all = load_json(META_PATH, {})
    indices_spec = load_json(INDICES_SPEC_PATH, {})
    css = extract_css(TEMPLATE_HTML)

    synced = []
    for slug, src_dir in sorted(reports.items()):
        fp = slug_dir_fingerprint(src_dir)
        dst_dir = os.path.join(DST_REPORTS, slug)
        dst_index = os.path.join(dst_dir, "index.html")
        prev = state.get(slug, {})
        if prev.get("fingerprint") == fp and os.path.exists(dst_index):
            log("UP-TO-DATE  %s" % slug)
            continue
        if os.path.exists(dst_index) and not state.get(slug):
            # Report already published on ByteMind but never tracked: baseline it so
            # only genuinely new/updated reports are re-converted in future runs.
            state[slug] = {
                "fingerprint": fp,
                "synced_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
                "baseline": True,
            }
            log("BASELINE    %s" % slug)
            continue

        meta = meta_all.get(slug, {})
        log("SYNCING     %s" % slug)
        if dry_run:
            synced.append(slug)
            continue

        os.makedirs(dst_dir, exist_ok=True)
        for sub in ("charts", "data", "scripts"):
            copy_tree(os.path.join(src_dir, sub), os.path.join(dst_dir, sub))
        summary_src = os.path.join(src_dir, "summary.html")
        if os.path.exists(summary_src):
            shutil.copy2(summary_src, os.path.join(dst_dir, "summary.html"))

        if not os.path.isdir(os.path.join(dst_dir, "_shared")):
            shutil.copytree(SHARED_SOURCE, os.path.join(dst_dir, "_shared"))

        for src, dst in (
            (CHART_DOWNLOAD_JS, os.path.join(DST_REPORTS, "chart-download.js")),
            (CHART_DOWNLOAD_CSS, os.path.join(DST_REPORTS, "chart-download.css")),
        ):
            if os.path.exists(src) and not os.path.exists(dst):
                shutil.copy2(src, dst)

        with open(os.path.join(src_dir, "index.html"), "r", encoding="utf-8") as f:
            src_html = f.read()
        title = convert_index(os.path.join(src_dir, "index.html"), dst_index, slug, meta, css)

        date = meta.get("date") or meta_date_to_iso(src_html)
        summary = meta.get("summary") or extract_exec_first_para(src_html)
        topics = meta.get("topics") or extract_toc(src_html)[:4]
        upsert_manifest(
            os.path.join(DST_REPORTS, "manifest.json"),
            {
                "filename": "%s/index.html" % slug,
                "title": meta.get("title") or title,
                "date": date,
                "summary": summary,
                "type": "report",
                "topics": topics,
            },
        )

        post_filename = generate_post(slug, meta, src_html, DST_POSTS)
        upsert_manifest(
            os.path.join(DST_POSTS, "manifest.json"),
            {
                "filename": post_filename,
                "title": meta.get("post_title") or meta.get("title") or title,
                "date": date,
                "summary": meta.get("post_summary") or summary,
            },
        )

        spec = indices_spec.get(slug, {})
        if spec:
            changed = apply_indices(slug, spec)
            if changed:
                log("  indices: " + ", ".join(changed))

        state[slug] = {
            "fingerprint": fp,
            "synced_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        }
        synced.append(slug)

    if not dry_run:
        save_json(STATE_PATH, state)

    log("")
    if dry_run:
        log("DRY RUN - would sync: %s" % (", ".join(sorted(synced)) or "nothing"))
    elif synced:
        log("Synced %d report(s): %s" % (len(synced), ", ".join(sorted(synced))))
    else:
        log("All reports up to date. Nothing to sync.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
