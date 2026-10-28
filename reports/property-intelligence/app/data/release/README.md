# Auckland Property Scout — public research release

Release: **20261028**  
Database build: **2026-10-28T07:25:13.547106+00:00**  
Code revision: **4daa42313af8211dadacb24fb0311a664dd0fa6c**

This bundle is a compact, reproducible snapshot of the Auckland Property Scout
research database. It contains derived listing facts, delisted history, model
predictions, dated price/change history, text features, topic/term associations and
aggregate metrics.

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
  "listings": 1048,
  "listing_snapshots": 6312,
  "listing_events": 186,
  "listing_price_history": 1066,
  "listing_price_dynamics": 1048,
  "model_predictions": 1522,
  "text_features": 1022,
  "text_term_associations": 98,
  "sales": 320
}
```
