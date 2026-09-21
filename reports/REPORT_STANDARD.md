# ByteMind Report Standard

Author: Dr Yuqian Zhang
Last updated: 10 July 2026

This document defines the required structure, layout, and build conventions for
analytical reports on the ByteMind website. It is derived from the two reference
reports in this project:

- `reports/property-market-analysis/`
- `reports/nz-tax-optimisation/`

Any new report must reproduce this architecture so that all reports share a
consistent look, structure, and set of features (tables, charts, callouts,
references, and downloadable data). When in doubt, open the two reference reports
and copy their patterns exactly.

---

## 1. Deliverable in one sentence

A self-contained, single-page HTML analytical brief with embedded CSS, interactive
ECharts visualisations, structured data tables, a references section with numbered
citations, and a downloadable data package with a methodology note, registered in
the site manifests so it appears on the Reports and Insights pages.

---

## 2. Folder structure (required)

Every report lives in its own folder under `reports/<report-slug>/` with this
exact layout:

```
reports/
  <report-slug>/
    index.html              The report: embedded CSS + content + chart containers
    assets/
      charts.js             All ECharts configurations for this report
    data/
      README.md             Sources and methodology for the data package
      figureN_<name>.csv    One CSV per figure (data behind each chart)
      <key_parameters>.csv  Master parameter/source file (see Section 9)
    _shared/
      js/
        echarts.min.js      The ECharts library (copy from an existing report)
      fonts/
        CrimsonPro-Regular.ttf
        CrimsonPro-Bold.ttf
        CrimsonPro-Italic.ttf
        InstrumentSans-Regular.ttf
        InstrumentSans-Bold.ttf
        InstrumentSans-Italic.ttf
        JetBrainsMono-Regular.ttf
        JetBrainsMono-Bold.ttf
```

Rules:
- `<report-slug>` is lower-case with hyphens, for example `nz-tax-optimisation`.
- The report entry file is always `index.html` so the URL is
  `www.bytemind.co.nz/reports/<report-slug>/`.
- Never use external CDNs or web fonts. Everything is self-hosted so the report
  works offline and does not break if a third party changes.
- To scaffold a new report, copy the `_shared/` folder from an existing report
  (do not regenerate the fonts or ECharts):
  `cp -r reports/property-market-analysis/_shared reports/<new-slug>/_shared`

---

## 3. Design system (CSS variables)

The `<head>` of `index.html` contains an embedded `<style>` block. Copy it wholesale
from a reference report. The design tokens are fixed and must not be changed
per-report:

```css
:root {
  --bg:    #fafaf9;   /* page background */
  --bg2:   #ffffff;   /* card / callout background */
  --ink:   #1a1a1a;   /* body text */
  --muted: #6b7280;   /* secondary text, axis labels */
  --rule:  #e5e7eb;   /* borders, gridlines */
  --accent:  #1e40af; /* primary: deep navy, headings, positive bars */
  --accent2: #b91c1c; /* secondary: red, warnings, negative bars */
}
```

Typography:
- Headings: `'Crimson Pro'` (serif).
- Body and UI: `'Instrument Sans'` (sans-serif).
- Monospace (code, if any): `'JetBrains Mono'`.
- Base body size 16px, line-height 1.7.
- Content column: `.container { max-width: 860px; margin: 0 auto; }`.

Declare all three fonts with `@font-face` pointing at `./_shared/fonts/...`, exactly
as in the reference reports.

---

## 4. Standard section order

Number the sections and keep this order. Property report and tax report both follow
it. Adjust the middle body sections to the topic, but keep the fixed bookends.

1. Cover (title, subtitle, author + date + "Analytical Brief")
2. (Optional) Scope and disclaimer callout, when the topic needs one (used in the
   tax report; recommended for anything advice-adjacent)
3. Executive Summary, including a metric-card row of 3 to 4 headline numbers
4. Body sections (the analysis: trends, metrics, comparisons, and so on)
5. Limitations / Predictive Uncertainty (honest discussion of what could be wrong)
6. Data, Sources, and Methodology (with the downloadable data table; see Section 8)
7. References (numbered `Sources` list in the footer; see Section 7)

The Data section is always the second to last, immediately before References.

---

## 5. Reusable content components

Use these building blocks (all defined in the shared CSS). Copy the markup exactly.

### Cover
```html
<header class="cover">
  <h1>Report Title<br>Second Line if Needed</h1>
  <p class="subtitle">One-line descriptive subtitle in italic serif</p>
  <p class="meta">Dr Yuqian Zhang &middot; 9 July 2026 &middot; Analytical Brief</p>
</header>
```

### Section headings
- `<h2>` for numbered top-level sections (navy underline rule applied by CSS).
- `<h3>` for subsections (for example `2.1 ...`).
- `<h4>` for small uppercase accent labels inside callouts.

### Key-point highlight
Wrap the single most important clause in a sentence to tint it navy:
```html
<mark class="key">the sentence that matters most</mark>
```
Use sparingly, at most one per paragraph.

### Metric cards (headline numbers)
Place a row of 3 to 4 in the Executive Summary.
```html
<div class="metric-row">
  <div class="metric-card">
    <div class="val">39%</div>            <!-- add class "warn" for red -->
    <div class="label">Short label<br>(source or period)</div>
  </div>
  ...
</div>
```

### Callout boxes
```html
<div class="callout">                      <!-- navy left border -->
  <h4>Callout heading</h4>
  <p>Explanatory note, observation, or worked example.</p>
</div>

<div class="callout warn">                 <!-- red left border, for risks/disclaimers -->
  <h4>Risk or disclaimer heading</h4>
  <p>...</p>
</div>
```

### Tables
Always wrap tables so they scroll on small screens:
```html
<div class="table-wrap">
  <table>
    <thead>
      <tr><th>Col A</th><th>Col B</th></tr>   <!-- navy header, white text -->
    </thead>
    <tbody>
      <tr><td>...</td><td>...</td></tr>       <!-- zebra striping via CSS -->
    </tbody>
  </table>
</div>
```

### Chart figures
Each chart is a `<figure>` with a numbered caption above an empty div that
charts.js targets by id:
```html
<figure class="chart-figure">
  <figcaption>Figure 1: Descriptive caption, including base year, units, and source.</figcaption>
  <div id="chart-real-hpi" style="width:100%;min-height:400px"></div>
</figure>
```
Caption rules: number every figure sequentially ("Figure 1", "Figure 2", ...),
state the unit and base year, note the source, and flag any approximation or
author computation directly in the caption.

---

## 6. Charts (ECharts) conventions

All chart logic goes in `assets/charts.js`, loaded at the end of `<body>` after
ECharts:
```html
<script src="./_shared/js/echarts.min.js"></script>
<script src="assets/charts.js"></script>
```

`charts.js` rules (follow the reference files exactly):
- Wrap everything in one IIFE: `(function() { ... })();`.
- Start with an author comment: `// charts.js -- <topic>` and
  `// Author: Dr Yuqian Zhang, <date>`.
- Read colours from the CSS variables so charts stay on-palette:
  ```js
  var style = getComputedStyle(document.documentElement);
  var accent  = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  ```
- Initialise each chart with the SVG renderer and animation off:
  `echarts.init(document.getElementById('chart-id'), null, { renderer: 'svg' });`
  and `setOption({ animation: false, ... })`.
- Wrap each chart in its own IIFE block with a header comment naming it.
- Add a resize handler for every chart:
  `window.addEventListener('resize', function() { chart.resize(); });`
- Colour convention: `accent` (navy) for primary series and positive values,
  `accent2` (red) for the second series, warnings, and negative values.
- Keep the raw data arrays inline in `charts.js`. These same numbers must be
  mirrored exactly in the corresponding `data/figureN_*.csv` (see Section 8).

Chart-type guidance (as used in the two reports):
- Long time series: smooth line, `symbol: 'none'`.
- Comparisons across categories: bar, colour-coded by sign or group.
- Two different units on one chart: dual `yAxis` (for example rate vs ratio).
- Ranking or peak-to-trough: horizontal bar with data labels.

---

## 7. References and citations

Two linked parts.

In-text citation (superscript link):
```html
...as documented by the BIS long series.<sup><a href="#cite-1">[1]</a></sup>
```

Footer source list (numbered, in a `<footer>`):
```html
<footer>
<div class="sources">
<h2>Sources</h2>
<ol>
  <li id="cite-1">
    <span class="src-title">Author/Publisher (Year). "Title." Short note on what it supports.</span>
    <a class="src-url" href="https://exact-url" target="_blank" rel="noopener">https://exact-url</a>
  </li>
  ...
</ol>
</div>
</footer>
```

Citation rules:
- Every `#cite-n` used in text must have a matching `<li id="cite-n">`, and every
  list item should be cited at least once. No gaps, no orphans.
- Prefer official primary sources (statistical agencies, regulators, legislation,
  official databases). Verify every URL resolves before publishing.
- Each source line states who, what, and a short note on the specific figure or
  claim it supports.

---

## 8. Data, Sources, and Methodology section

This is the standard section that makes every chart's data downloadable. It has two
subsections and a download table.

Structure:
```
## N. Data, Sources, and Methodology
   Intro paragraph: state that data is downloadable and honestly classify the
   series (see provenance categories below).

### N.1 How the series/figures are constructed
   One short paragraph per figure or figure group explaining the calculation,
   units, base year, and any filter or transformation. Include a worked check
   where a number can be verified against an official example.

### N.2 Downloadable data
   A <div class="table-wrap"><table> with columns: Dataset | Figure | Download.
   Each Download cell is: <a href="data/figureN_name.csv" download>figureN_name.csv</a>
   Include a final row linking the data README.md.
```

Provenance honesty (required): classify each series as one of:
1. Indicative points read from an official series (faithful to the published
   series but not the full-resolution file; link the source for the full data).
2. Author computation (for example an HP-filtered trend or z-scores). State the
   method and parameters.
3. Illustrative comparison (for example event-based or episode-based charts).
   State that it is a comparison, not a continuous series.

Never present reconstructed or indicative points as if they were a raw official
download. Mark ongoing or provisional values clearly (for example with an asterisk
and a note).

---

## 9. Data package conventions (the `data/` folder)

- One CSV per figure, named `figureN_<short_name>.csv`, where N matches the figure
  number in the report.
- Column headers are lower_snake_case and include units in the name where helpful
  (for example `nz_real_hpi_index_2010_100`, `marginal_rate_pct`).
- The CSV values must match the arrays plotted in `charts.js` exactly.
- Include a master file that lists every headline parameter or every series with
  its source and URL:
  - For rate/threshold reports: `key_<topic>_parameters.csv` with columns
    `parameter,value,unit,applicable_period,source,source_url`.
  - For data-series reports: `figure_sources_and_methodology.csv` with columns
    `figure,series,unit,frequency,coverage,primary_source,source_url,construction_note`.
- Include `data/README.md` documenting: the provenance categories, a file table,
  the primary sources with URLs, the methodology for any computed series, a
  reproducibility note, and a disclaimer. Head it with author and date.
- Quote any CSV field that contains a comma, using standard double quotes.

---

## 10. Registration (so the report appears on the site)

After the report is built, register it. Both manifests are JSON arrays; append a
new object (mind the commas, keep valid JSON).

`reports/manifest.json`:
```json
{
  "filename": "<report-slug>/index.html",
  "title": "Report Title",
  "date": "YYYY-MM-DD",
  "summary": "One or two sentence summary.",
  "type": "report",
  "topics": ["Topic A", "Topic B", "Topic C"]
}
```

Optional but recommended: a short summary post in `posts/` that links to the full
report, registered in `posts/manifest.json`:
```json
{
  "filename": "YYYY-MM-DD-<slug>.md",
  "title": "Post Title",
  "date": "YYYY-MM-DD",
  "summary": "One sentence."
}
```
The post markdown links to the report with `[Read the full analytical brief](/reports/<report-slug>/)`.

Validate both manifests after editing:
`node -e "JSON.parse(require('fs').readFileSync('reports/manifest.json'));JSON.parse(require('fs').readFileSync('posts/manifest.json'));console.log('valid')"`

---

## 11. Writing and house style

- Language: English with New Zealand / Australian spelling.
- Do not use em dashes. Use commas, colons, or full stops.
- Do not use emojis.
- Plain, precise, professional prose. Avoid cliches and dramatic phrasing.
- Author attribution: "Dr Yuqian Zhang" on the cover meta line and in the
  `charts.js` header comment; include the report date.
- For advice-adjacent topics (tax, finance, legal), include a scope and disclaimer
  callout near the top stating that the report is general information, not advice.
- State uncertainty honestly in the Limitations section.

---

## 12. Accuracy and review workflow

Before publishing, run the checks that were applied to the two reference reports:

1. Facts: verify every rate, threshold, and figure against an official primary
   source. Prefer regulators, statistical agencies, and legislation.
2. Links: fetch every reference URL and confirm it resolves to the correct page.
   Replace moved or broken links with the current canonical URL.
3. Arithmetic: recompute every derived figure. Where possible, check one value
   against an official worked example.
4. Data parity: confirm each `data/figureN_*.csv` matches the arrays in
   `charts.js` exactly.
5. Structure: confirm balanced HTML tags, that every `chart-*` container has a
   matching `echarts.init`, and that every citation maps to a source.
6. Review the whole report 2 to 3 times for consistency before sign-off.

Local preview:
```bash
python3 -m http.server 8000        # then open http://localhost:8000/reports/<slug>/
```

---

## 13. Deployment

The site auto-deploys from the `main` branch via GitHub Pages. After building and
reviewing:
```bash
git add reports/<report-slug>/ reports/manifest.json posts/manifest.json posts/<post>.md
git commit -m "Add <topic> report"
git push origin main
```
Wait 1 to 2 minutes, then hard-refresh the live page (Cmd + Shift + R) to bypass
browser cache. Confirm the report and its data files load, and that the report
appears on the Reports page.

---

## 14. Quick checklist for a new report

- [ ] Folder `reports/<slug>/` created; `_shared/` copied from an existing report
- [ ] `index.html` uses the shared CSS design system unchanged
- [ ] Sections numbered in the standard order (cover to references)
- [ ] Executive summary with a 3 to 4 metric-card row
- [ ] Charts in `assets/charts.js` following the IIFE + SVG + resize pattern
- [ ] Every figure captioned with unit, base year, source, and any caveat
- [ ] One CSV per figure in `data/`, values matching `charts.js`
- [ ] Master parameter/source CSV and `data/README.md` written
- [ ] Data, Sources, and Methodology section with the download table
- [ ] References section with matching `#cite-n` links
- [ ] Registered in `reports/manifest.json` (and optional post + `posts/manifest.json`)
- [ ] Manifests validated as JSON
- [ ] Accuracy, links, arithmetic, and data-parity checks passed; reviewed 2 to 3 times
- [ ] Committed and pushed; verified live after cache refresh
```
