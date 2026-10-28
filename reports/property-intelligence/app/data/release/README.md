# Auckland Property Scout — public research release

Release: **20261029**  
Database build: **2026-10-28T18:48:49.881316+00:00**  
Code revision: **a1a779f115cc31d9b3732ca1802e9012755832c2**

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
  "listings": 1073,
  "listing_snapshots": 7358,
  "listing_events": 611,
  "listing_price_history": 1104,
  "listing_price_dynamics": 1073,
  "property_sales": 1502,
  "listing_signals": 1073,
  "listing_sale_outcomes": 4,
  "sale_feedback_calibration": 6,
  "model_predictions": 2579,
  "text_features": 1047,
  "text_term_associations": 97,
  "sales": 328
}
```
