# Data for "Tax Optimisation for New Zealand SMEs and Their Owners"

Author: Dr Yuqian Zhang
Date: 9 July 2026

This folder contains the structured datasets underlying the figures and headline
statistics in the report `../index.html`. Every value is either a statutory rate
or threshold taken directly from an official source, or a figure computed
deterministically from those statutory parameters using the method described
below. No survey data, estimated data, or third-party proprietary data is used.

## Files

| File | Used in | Contents |
|---|---|---|
| `key_tax_parameters_2025_26.csv` | Whole report | Master list of every headline rate and threshold, with applicable period and official source URL |
| `table1_personal_tax_brackets_2025_26.csv` | Section 2.1 table | The five 2025/26 personal income tax bands and tax on each full band |
| `figure1_marginal_effective_rates_2025_26.csv` | Figure 1 | Marginal and effective (average) income tax rate by income level |
| `figure2_entity_tax_comparison.csv` | Figure 2 | Current-year tax on $250,000 profit under three structures |
| `figure3_investment_boost_year_one.csv` | Figure 3 | Year-one deduction on a $100,000 asset with and without Investment Boost |
| `figure4_kiwisaver_default_rate.csv` | Figure 4 | Default minimum KiwiSaver contribution rate by effective date |
| `figure5_headline_rates_by_vehicle.csv` | Figure 5 | Headline tax rate on each income vehicle |

## Sources

All statutory parameters come from Inland Revenue (IRD), the Income Tax Act 2007,
the Goods and Services Tax Act 1985, and official Budget 2025 material. The exact
page and URL for each parameter is recorded in the `source` and `source_url`
columns of `key_tax_parameters_2025_26.csv`. All URLs were verified as live and
correct on 9 July 2026.

## Methodology

The report contains no scraped or sampled data. Two kinds of value appear:

1. Statutory parameters (rates, thresholds, dates). These are transcribed
   directly from the official source listed against each parameter. They are not
   calculated or estimated.

2. Derived figures. These are computed by applying the statutory parameters
   using standard New Zealand income tax arithmetic. The calculations are:

### Personal income tax (Table 1, Figure 1)

New Zealand uses a progressive scale with no tax-free threshold. Tax is the sum
across bands of (income taxed in each band) x (band rate), using the 2025/26
brackets:

- 10.5% on $0 to $15,600
- 17.5% on $15,601 to $53,500
- 30% on $53,501 to $78,100
- 33% on $78,101 to $180,000
- 39% above $180,000

Worked check: tax on $60,000 = 15,600 x 0.105 + (53,500 - 15,600) x 0.175 +
(60,000 - 53,500) x 0.30 = 1,638 + 6,632.50 + 1,950 = $10,220.50. This matches
IRD's own published worked example for a $60,000 earner.

The effective (average) rate in Figure 1 is cumulative income tax divided by
income. Figures exclude the ACC earners' levy, which is charged separately (see
`key_tax_parameters_2025_26.csv`).

### Entity comparison (Figure 2)

On $250,000 of profit for a single owner, income tax only, no other income:

- Sole trader: full $250,000 at personal rates = $76,577.50.
- Company retaining all profit: $250,000 x 28% = $70,000 (a deferral, not a
  permanent saving; distribution to a 39% shareholder adds an 11 percentage
  point dividend top-up).
- Salary $180,000 plus $70,000 retained: personal tax on $180,000 =
  $49,277.50, plus $70,000 x 28% = $19,600, total $68,877.50.

### Investment Boost (Figure 3)

Illustrative $100,000 eligible asset with a 10% diminishing-value depreciation
rate:

- Without Investment Boost: year-one deduction = $100,000 x 10% = $10,000.
- With Investment Boost: 20% upfront = $20,000, then 10% depreciation on the
  remaining $80,000 = $8,000, giving a year-one deduction of $28,000.

Total deductions over the asset's life are unchanged; the Boost brings deductions
forward (a timing benefit).

### KiwiSaver and headline rates (Figures 4 and 5)

These are direct transcriptions of statutory rates; no calculation is involved.
Figure 5's "company profit distributed to top shareholder" value of 39% reflects
28% company tax grossed up by the imputation credit and topped up to the 39%
shareholder rate.

## Reproducibility

All derived figures can be reproduced from the statutory parameters in
`key_tax_parameters_2025_26.csv` using the arithmetic above. No random processes,
seeds, or external data pipelines are involved. All monetary values are in New
Zealand dollars.

## Disclaimer

These datasets support a general-information report and do not constitute tax
advice. Rates and thresholds change frequently. Confirm current figures on
ird.govt.nz before relying on them.
