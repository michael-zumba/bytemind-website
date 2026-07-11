# Data Package: NZ First-Home Buyers and the Property Market

Author: Dr Yuqian Zhang
Date: 11 July 2026
Report: NZ First-Home Buyers and the Property Market: Testing the Common Assumptions

---

## Provenance Categories

The data in this package falls into three categories:

1. **Indicative points read from an official series.** These datasets reproduce the profile of official data series at annual (or quarterly) resolution. The numbers are faithful to the published series as of the date of compilation, but they are not full-resolution official downloads. For the authoritative series in its full frequency, use the source URLs in the figures below or in `figure_sources_and_methodology.csv`.

2. **Author compilation from multiple public sources.** The FHB characteristics data (Figure 10) and the LVR timeline are assembled from multiple official and industry reports into a consistent annual format. The individual data points are attributed to their sources, but the compilation format is the author's.

3. **Illustrative timeline.** The LVR timeline (`lvr_timeline.csv`) records policy events rather than a statistical series. It is included for reference alongside the main figures.

---

## File Table

| File | Figure | Description | Primary Source |
|---|---|---|---|
| `figure1_fhb_share_purchases.csv` | Figure 1 | First-home buyer share of property purchases, 2016-2025 | CoreLogic/Cotality |
| `figure2_national_prices.csv` | Figure 2 | National median house price and REINZ HPI, 2016-2026 | REINZ |
| `figure3_regional_medians.csv` | Figure 3 | Median house prices by region, 2017-2025 | REINZ |
| `figure4_days_to_sell.csv` | Figure 4 | Median days to sell, 2018-2025 | REINZ |
| `figure5_sales_volumes.csv` | Figure 5 | Annual sales volumes, 2018-2025 | REINZ |
| `figure6_overseas_buyer_share.csv` | Figure 6 | Overseas buyer share of home transfers, 2017-2024 | Stats NZ |
| `figure7_ocr_and_mortgage_rates.csv` | Figure 7 | OCR and 1-year special mortgage rates, 2016-2026 | RBNZ |
| `figure8_net_migration.csv` | Figure 8 | Net migration by citizenship, 2016-2025 | Stats NZ |
| `figure9_building_consents.csv` | Figure 9 | New dwellings consented annually, 2016-2025 | Stats NZ |
| `figure10_fhb_characteristics.csv` | Figure 10 | FHB age, median price, and KiwiSaver withdrawals, 2019-2026 | Cotality, CoreLogic, FMA |
| `lvr_timeline.csv` | Supporting data | LVR restriction timeline, 2013-2025 | RBNZ |
| `figure_sources_and_methodology.csv` | All figures | Source, URL, and methodology note for every series | Multiple |

---

## Primary Sources

- **CoreLogic/Cotality** (NZ Buyer Classification, First Home Buyer Reports): https://www.cotality.com/nz/insights/
- **REINZ** (HPI reports, monthly property data): https://www.reinz.co.nz/
- **Stats NZ** (Property Transfer Statistics, Building Consents, International Migration): https://www.stats.govt.nz/
- **Reserve Bank of New Zealand** (OCR, mortgage rates, LVR timeline): https://www.rbnz.govt.nz/
- **Financial Markets Authority** (KiwiSaver Annual Report): https://www.fma.govt.nz/
- **Inland Revenue** (KiwiSaver withdrawal statistics): https://www.ird.govt.nz/
- **Kainga Ora** (First Home Loan, Home Ownership Products): https://kaingaora.govt.nz/

---

## Methodology for Computed Series

- **Regional median prices (Figure 3)**: Where regional monthly medians are available from interest.co.nz charts, annual figures are estimated from monthly values. For years where exact medians are not retrievable from public sources, values are approximated from REINZ press releases and are marked with a note in the source column.

- **Net migration by citizenship (Figure 8)**: Non-NZ citizen net migration is calculated as total net migration minus NZ citizen net migration, both from Stats NZ outcomes-based series. 2025 data are provisional.

- **Annual medians (Figures 4 and 5)**: Where annual summaries are reported as averages of monthly values, the summed or median values are calculated from the underlying monthly data from interest.co.nz. Some annual values may differ slightly from REINZ official annual totals due to data revision schedules.

---

## Reproducibility

- All data series are derived from publicly available sources as of July 2026. URLs were verified as live on 11 July 2026.
- Figures labelled as "approximate" (~) in the CSV source columns indicate values derived from published percentage changes or regional breakdowns rather than from the exact official total.
- Charts.js contains the same data arrays plotted in each figure. The CSV values and charts.js arrays should match exactly. If discrepancies are found, the CSV is the more recent compilation.
- For the full-resolution official series, use the source URLs provided in `figure_sources_and_methodology.csv`.

---

## Disclaimer

This data package is provided as a supplementary resource to the analytical brief. It is not a substitute for official statistical releases. Users requiring exact values for research or policy purposes should download the full series directly from the primary sources listed above. The author accepts no liability for errors in compilation or for decisions made based on this data.
