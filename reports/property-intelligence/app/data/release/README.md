# Auckland Property Scout — public research release

Release: **20261101**  
Database build: **2026-10-31T20:01:31.702044+00:00**  
Code revision: **0a3b7f7667cb37701463d521e280e5c65c1dcd70**

This bundle is a compact, reproducible snapshot of the Auckland Property Scout
research database. It contains derived listing facts, delisted history, model
predictions, dated price/change history, text features, topic/term associations and
aggregate metrics.

## Files

- `auckland_property.sqlite.gz` — full compact SQLite database (canonical release)
- `*.csv.gz` — table extracts for quick analysis
- `schema.sql` — database schema
- `manifest.json` — checksums, counts and provenance
- `auckland_property_release.zip` — all of the above in one download
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
  "listings": 1106,
  "listing_snapshots": 10523,
  "listing_events": 894,
  "listing_price_history": 1173,
  "listing_price_dynamics": 1106,
  "property_sales": 1546,
  "listing_signals": 1106,
  "listing_sale_outcomes": 1,
  "sale_feedback_calibration": 4,
  "model_predictions": 2629,
  "text_features": 1079,
  "text_term_associations": 102,
  "sales": 311
}
```
