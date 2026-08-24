# ByteMind Website

This repository contains the source code for the ByteMind Ltd website (www.bytemind.co.nz).
The website is a static site (HTML/CSS/JS) hosted on GitHub Pages, designed for performance, security, and ease of maintenance without backend dependencies.

## Positioning

ByteMind Ltd is a **boutique consulting firm** specialising in business analytics, digital transformation, and strategic advisory for professional services (accounting, tax, finance). The firm contracts with professional bodies (including CPA Australia) and serves clients across New Zealand, Australia, and the Asia-Pacific region. The website functions as a credibility platform, a content hub for proprietary research, and a lead-generation channel.

## Structure

*   `index.html`: Home page.
*   `services.html`: Services page (Business Analytics, Global Growth Roadmap, Fractional Tax Director, SME Health Check, Digital Transformation Advisory).
*   `indices.html`: Housing Market Indicators (interactive ECharts, data from BIS, OECD, RBNZ, Stats NZ).
*   `insights.html`: Short-form articles and tax updates.
*   `reports.html`: Deep analytical reports (distinct from shorter Insights articles).
*   `about.html`: About page.
*   `contact.html`: Contact page.
*   `assets/`: CSS (modern design system), JS (interactive logic), Images, Logos.
*   `data/`: Data files (CSV/TXT) for Economic Indices.
*   `posts/`: Markdown files for "Latest Insights" (short-form articles).
*   `reports/`: Self-contained HTML reports for deep analytical briefs (long-form, with interactive charts).

## How to Update Content

### 1. Adding a New Insight (Blog Post)
1.  **Create File**: Add your markdown file (e.g., `YYYY-MM-DD-title.md`) to the `posts/` folder.
    *   *Tip: You can include a YAML frontmatter block at the top, though the current viewer strips it.*
2.  **Update Manifest**: Open `posts/manifest.json` and add an entry for the new post:
    ```json
    {
        "filename": "YYYY-MM-DD-title.md",
        "title": "Your Title Here",
        "date": "Month DD, YYYY",
        "summary": "A brief summary of the post..."
    }
    ```
    *   *Note: Ensure the JSON syntax is valid (commas between objects).*

### 2. Adding a New Research Report
Research reports are deep analytical briefs (HTML format, with interactive charts) that appear on the Reports page. They are distinct from shorter Insights articles.

1.  **Create the report**: Your AI agent should produce a self-contained HTML report with all assets (CSS, JS, fonts, charts) in its own subfolder under `reports/`. See `reports/property-market-analysis/` for an example structure.
    ```
    reports/
      your-report-name/
        index.html          (the report itself)
        assets/
          charts.js         (any chart data/configuration)
        _shared/
          js/               (libraries like echarts.min.js)
          fonts/            (self-hosted fonts)
    ```
2.  **Register the report**: Open `reports/manifest.json` and add an entry:
    ```json
    {
        "filename": "your-report-name/index.html",
        "title": "Your Report Title",
        "date": "YYYY-MM-DD",
        "summary": "A brief summary of the report...",
        "type": "report",
        "topics": ["Topic A", "Topic B"]
    }
    ```
3.  **(Optional) Create a summary post**: Add a Markdown file in `posts/` that summarises the key findings and links to the full report. Register it in `posts/manifest.json` as usual. This surfaces the report on the Insights page and the home page while directing readers to the full version.

### 3. Updating Indices Data
*   **Real House Prices:** Update `data/nz_au_real_hpi.csv`. Data is also stored inline in `assets/js/indices.js` for offline reliability.
*   **Valuation Metrics:** Update `data/nz_valuation_metrics.csv` (price-to-income, real HPI deviation, mortgage rates, household DTI).
*   **Supply & Demographics:** Update `data/nz_supply_demographics.csv` (building consents, net migration).
*   **International Comparison:** Update `data/international_comparison.csv`.

### 4. Automated Sync from the Personal Website

Research briefs published on the personal website
(`~/Python Projects/Personal/Personal website/public/reports/<slug>/`) can be
synced here automatically. The sync script converts each report into the
ByteMind format, registers it in the manifests, generates an Insights summary
post, and updates the Indices page panels and sitemap.

```bash
python3 scripts/sync_from_personal.py            # sync new/updated reports
python3 scripts/sync_from_personal.py --dry-run  # preview without changes
python3 scripts/sync_from_personal.py --force <slug>  # re-convert one report
```

How it decides what to sync:
*   A report is new if `reports/<slug>/index.html` does not exist yet.
*   A report is updated if the fingerprint of the personal report folder
    (all files, sizes, and mtimes) differs from `reports/.sync-state.json`.
*   Reports already published on ByteMind are baselined on first run and only
    re-converted when the personal source changes.

What the script touches:
*   `reports/<slug>/` — converted `index.html` (ByteMind design system,
    self-hosted fonts/echarts, Key Terms callout, footer navigation),
    copied `charts/`, `data/`, `scripts/`, `summary.html`, and `_shared/`.
*   `reports/manifest.json` — Reports page entry.
*   `posts/<date>-<slug>.md` + `posts/manifest.json` — Insights page entry.
*   `indices.html` + `assets/js/indices.js` — research-indicator panels,
    metric tiles, and "Read the full reports" cards, driven by
    `reports/.sync-indices.json`.
*   `sitemap.xml` — new report URLs.

Curated metadata (titles, summaries, topics, Key Terms, and Indices panel
config) lives in `reports/.sync-meta.json` and `reports/.sync-indices.json`.
Add an entry there when a report needs a custom summary or indicator panels;
otherwise the script derives defaults from the report HTML.

### 5. Modifying Design
*   Edit `assets/style.css`. The site uses a variable-based design system (`:root`) for colors, spacing, and shadows.
*   Common variables: `--primary`, `--accent`, `--bg-body`.

## Local Development
Since this is a static site, you can view it locally. However, due to browser security policies (CORS), fetching local JSON/CSV files might be blocked if you just open the file directly.

**Recommended:** Run a simple local server.
```bash
python3 -m http.server 8000
```
Then visit `http://localhost:8000`.

## Deployment

The site is hosted via **GitHub Pages**.

### Updating the Live Site

The site uses continuous deployment through GitHub Pages. This means that as soon as you push code changes to the `main` branch, GitHub automatically rebuilds and publishes the website online.

Here is the step-by-step process to push your changes:

1.  **Open the Terminal**: Open a terminal window in your IDE (like VS Code or Trae) and make sure you are in the `ByteMind_Website` directory.
    ```bash
    cd "/Users/zhangy6j/Python Projects/Personal/ByteMind Project/ByteMind_Website"
    ```

2.  **Stage your changes**: Tell Git which files you want to include in the update. The `.` means "include everything that changed".
    ```bash
    git add .
    ```

3.  **Commit your changes**: Package the changes with a descriptive message of what you did.
    ```bash
    git commit -m "Describe your changes here (e.g., Added new tax article)"
    ```

4.  **Push to the live website**: Send the packaged changes to the GitHub repository. This triggers the website update.
    ```bash
    git push origin main
    ```

*(Alternatively, you can combine these steps into one quick command:)*
```bash
git add . && git commit -m "Update website content" && git push origin main
```

**What happens next?**
After running `git push`, wait about **1-2 minutes**. GitHub Pages will automatically process the files and deploy the site. Refresh `www.bytemind.co.nz` in your browser to see your updates live!

### First-Time Setup (If not already configured)
1.  Go to the repository on GitHub.
2.  Navigate to **Settings** > **Pages**.
3.  Under **Build and deployment**:
    *   **Source**: Select `Deploy from a branch`.
    *   **Branch**: Select `main` and folder `/ (root)`.
4.  Click **Save**.
5.  (Optional) Under **Custom domain**, enter `www.bytemind.co.nz` and save. Ensure your DNS provider has a CNAME record pointing to `<username>.github.io`.
