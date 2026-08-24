# Scheduled Task: Sync Personal Website Reports to ByteMind

This file documents the scheduled task that keeps the ByteMind website in sync
with research briefs published on the personal website. It is a human-readable
spec only; the automation itself is created through the Codex / ChatGPT desktop
app (**Scheduled** sidebar) or by asking Codex to create it.

## Parameters

| Field | Value |
| --- | --- |
| Name | `Sync personal website reports to ByteMind` |
| Schedule | Daily at 9:00 AM (Pacific/Auckland), i.e. `FREQ=DAILY;BYHOUR=9;BYMINUTE=0` |
| Kind | Heartbeat attached to the current local thread (or a cron job against the ByteMind project if a standalone task per run is preferred) |
| Status | ACTIVE |

## Prompt

```
Check the personal website at '/Users/zhangy6j/Python Projects/Personal/Personal website'
for new or updated research briefs under public/reports/<slug>/ (any folder containing
index.html). If the ByteMind website at '/Users/zhangy6j/Python Projects/Personal/ByteMind
Project/ByteMind_Website' is missing the report or its copy is outdated, sync it by running
'python3 scripts/sync_from_personal.py' from the ByteMind website root (the script already
uses absolute paths). After syncing, verify the changes locally: JSON manifests parse, the
new report page loads with its charts initialized, and indices.html, insights.html and
reports.html reflect the new report. If verification passes, commit the changes in the
ByteMind git repository with a clear message and push to origin/main so the live site
updates. If the script reports 'All reports up to date' and nothing changed, do nothing
further. Report a concise summary of what was synced, verified and deployed, or state that
nothing changed.
```

## How the sync works

`python3 scripts/sync_from_personal.py` detects reports that are new (no
`reports/<slug>/` in ByteMind) or updated (fingerprint of the personal report
folder differs from `reports/.sync-state.json`), then:

1. Converts `index.html` into the ByteMind template (self-hosted fonts/ECharts,
   Key Terms callout, table of contents, footer navigation, ByteMind citations).
2. Copies `charts/`, `data/`, `scripts/`, `summary.html` and `_shared/`.
3. Registers the report in `reports/manifest.json` (Reports page).
4. Generates an Insights summary post in `posts/` and registers it in
   `posts/manifest.json` (Insights page).
5. Adds research-indicator panels, metric tiles and report cards to
   `indices.html` + `assets/js/indices.js` via `reports/.sync-indices.json`.
6. Adds the report URL to `sitemap.xml`.

Preview with `--dry-run`; force re-conversion with `--force <slug>`.
