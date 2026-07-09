# Data for "Long-Run Property Market Trends in New Zealand and Australia"

Author: Dr Yuqian Zhang
Date: 8 July 2026 (data package added 9 July 2026)

This folder contains the datasets underlying the eight figures in the report
`../index.html`. It is provided so the charts can be inspected, downloaded, and
reused, and so the construction of each series is transparent.

## Important note on data provenance

This is an analytical brief, not a raw data release. The figures combine three
kinds of series, and it is important not to confuse them:

1. Indicative points from official series. Several charts plot annual points
   read from official long-run series (BIS, OECD, RBNZ, Stats NZ) to show the
   shape and turning points of the data over decades. These are faithful to the
   published series but are not the complete, full-frequency official files. For
   the authoritative, full-resolution data, download directly from the source
   URLs listed in `figure_sources_and_methodology.csv`.

2. Author computations. Figure 4 (deviation from trend) and Figure 5
   (valuation z-scores) are computed by the author from the underlying series
   using the methods described below. They are analytical constructs, not
   published indicators.

3. Illustrative comparisons. Figure 2 (policy milestones) compares the
   approximate real price change around discrete policy events; the events are
   not evenly spaced in time and the chart is a comparison, not a continuous
   time series. Figure 8 (international declines) reports peak-to-trough real
   declines by episode, with New Zealand and Australia marked with an asterisk
   because their corrections were still ongoing at the time of writing.

Every series, its unit, frequency, source, source URL, and construction note is
recorded row by row in `figure_sources_and_methodology.csv`.

## Files

| File | Figure | Contents |
|---|---|---|
| `figure_sources_and_methodology.csv` | All | Source, URL, and construction note for every series |
| `figure1_real_house_price_index_nz_au.csv` | Figure 1 | NZ and AU real house price index (2010=100), 1970-2025 |
| `figure2_policy_milestone_real_growth.csv` | Figure 2 | NZ real HPI growth around selected policy events |
| `figure3_price_to_income_nz.csv` | Figure 3 | NZ price-to-income ratio (2015=100) and long-run median |
| `figure4_real_price_deviation_from_trend_nz.csv` | Figure 4 | NZ real HPI deviation from HP-filtered trend (%) |
| `figure5_valuation_zscores.csv` | Figure 5 | Composite valuation z-scores, current vs 2021 peak |
| `figure6_mortgage_rate_and_dti_nz.csv` | Figure 6 | NZ 1-year fixed mortgage rate and household DTI |
| `figure7_building_consents_and_migration_nz.csv` | Figure 7 | NZ building consents and net migration |
| `figure8_international_real_price_declines.csv` | Figure 8 | Peak-to-trough real house price declines by country |

## Primary sources

- Bank for International Settlements (BIS), Residential Property Price
  Statistics, long series on real house prices (deflated by CPI, 2010=100).
  https://www.bis.org/statistics/pp_residential_2602.htm and the BIS Data Portal
  https://data.bis.org/topics/RPP
- OECD Analytical house price indicators (price-to-income and price-to-rent,
  2015=100). https://www.oecd.org/en/data/indicators/housing-prices.html
- Reserve Bank of New Zealand (RBNZ): B20 mortgage interest rates
  https://www.rbnz.govt.nz/statistics/series/exchange-and-interest-rates/new-residential-mortgage-standard-interest-rates
  and household debt key statistics
  https://www.rbnz.govt.nz/statistics/key-statistics/household-debt
- Stats NZ / Tatauranga Aotearoa: building consents and international migration.
  https://www.stats.govt.nz/topics/building/

These match the source list in the report's reference section, which also cites
the RBNZ Financial Stability Report, RBA Financial Stability Review, IMF Article
IV, Demographia, and the Jorda-Schularick-Taylor macrohistory literature for the
narrative claims.

## Methodology for computed series

### Real house prices (Figures 1, 2, 8)

Real house prices are nominal prices deflated by the consumer price index, on the
BIS harmonised basis with 2010=100. The annual points reproduce the profile of
the BIS long real series for New Zealand and Australia.

### Price-to-income ratio and long-run median (Figure 3)

The price-to-income ratio is the OECD analytical indicator (nominal house prices
divided by nominal disposable income per capita, indexed to 2015=100). The dashed
line is the median of the plotted series (88.9), used as a simple long-run
reference level.

### Deviation from trend (Figure 4)

The trend is estimated with a one-sided Hodrick-Prescott filter applied to the
real house price series, using a smoothing parameter lambda = 400,000, consistent
with the BIS convention for credit-gap style calculations on long series. The
deviation is (real HPI minus filtered trend) as a percentage of the trend. Because
the HP filter adapts to structural shifts, part of a sustained level shift is
absorbed into the trend, so the deviation should be read as indicative of cyclical
position rather than a precise measure of over or undervaluation.

### Valuation z-scores (Figure 5)

For each of four metrics (price-to-income, price-to-rent, real HPI deviation from
trend, and household debt-to-income), the z-score is (value minus the series mean)
divided by the series standard deviation, computed over the available sample. Two
snapshots are shown: the Q4 2021 peak and Q1 2025. Z-scores summarise how far each
metric sat above its own historical norm at each date.

### Mortgage rate and DTI (Figure 6), consents and migration (Figure 7)

These reproduce the profile of the RBNZ and Stats NZ series at annual frequency.
The mortgage rate is the 1-year fixed carded rate; DTI is household debt as a
percentage of disposable income; consents are dwelling consents issued; migration
is annual net permanent and long-term migration.

## Reproducibility and limitations

The computed series (Figures 4 and 5) can be reproduced from the underlying BIS,
OECD, and RBNZ data using the formulas above. The indicative annual points are
intended for visualisation of long-run trends; for statistical work, download the
full-resolution series from the official source URLs. All values are as plotted in
the report as at 8 July 2026 and reflect data vintages available at that date.

## Disclaimer

This data package supports a general analytical brief and does not constitute
financial advice. Housing data are revised over time and definitions differ across
countries; consult the primary sources for authoritative, current figures.
