# Auckland Property Scout — public research release

Release: **20261027**  
Database build: **2026-10-27T08:05:06.090886+00:00**  
Code revision: **708132f32c89def34b15f91a172cf99167b69af1**

This bundle is a compact, reproducible snapshot of the Auckland Property Scout
research database. It contains derived listing facts, delisted history, model
predictions, text features, topic/term associations and aggregate metrics.

## Files

- `auckland_property.sqlite.gz` — full compact SQLite database (canonical release)
- `*.csv.gz` — table extracts for quick analysis
- `schema.sql` — database schema
- `manifest.json` — checksums, counts and provenance
- `LICENSE.md` — data/code licensing and source attribution

## Verify

```bash
python -m release.verify --release .
```

## Reproduce

```bash
python -m pip install pandas numpy scikit-learn statsmodels
gunzip -c auckland_property.sqlite.gz > auckland_property.sqlite
python3 -m release.verify --release .
```

The release deliberately omits raw Trade Me descriptions, photos, agent contact
details and member IDs. Those remain in the private working cache; publishing them
would redistribute third-party page content. Derived text features and topics are
included so the value-language analysis can be inspected and rerun from the
released tables.

## Counts

```json
{
  "listings": 1022,
  "listing_snapshots": 5279,
  "listing_events": 123,
  "model_predictions": 1483,
  "text_features": 996,
  "text_term_associations": 96,
  "sales": 315
}
```
