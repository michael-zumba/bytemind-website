# Data Package: Lotto NZ -- Two Lenses of Probability

Author: Dr Yuqian Zhang
Date: 20 July 2026
Report: Lotto NZ: Two Lenses of Probability

---

## Provenance Categories

The data in this package falls into three categories:

1. **Published official odds.** The probabilities and odds in `figure1_lotto_odds.csv` are taken directly from Lotto NZ's published game information on mylotto.co.nz. These values are not computed; they are the official game parameters as disclosed to players.

2. **Compiled from primary sources.** `figure2_powerball_jackpot_history.csv` combines published jackpot results from lotto.net with the author's construction of rollover chains consistent with Lotto NZ's draw schedule (104 draws per year, Wednesdays and Saturdays). Key dates (won amounts) are verified against public results; intermediate rollover amounts are estimated from the typical growth rate of $1M to $3M per rollover.

3. **Computed values.** Probabilities in `figure3_probability_comparison.csv` and `key_parameters.csv` are computed from the published odds using standard combinatorial probability, except for the market-level estimates which are derived from Lotto NZ's published FY2024 sales and jackpot frequency data.

---

## File Table

| File | Figure | Description | Primary Source |
|---|---|---|---|
| `figure1_lotto_odds.csv` | Figure 1 | Published odds for all Lotto, Powerball, and Strike divisions | mylotto.co.nz |
| `figure2_powerball_jackpot_history.csv` | Figure 2 | Powerball jackpot amounts and rollover status, Jan 2025 to Jun 2026 | lotto.net (won amounts), author construction (rollover chains) |
| `figure3_probability_comparison.csv` | Figure 3 | Probability scenarios comparing unconditional, participation-adjusted, and market-level perspectives | Computed from published odds and Lotto NZ sales data |
| `key_parameters.csv` | All figures | Master parameters: ticket prices, sales, community returns, and key game mechanics | Lotto NZ Integrated Report 2023/24; mylotto.co.nz |

---

## Primary Sources

- **Lotto NZ (mylotto.co.nz)** -- Published game odds, division structures, ticket pricing, and draw schedule.
- **Lotto NZ Integrated Report 2023/24** -- Total sales ($1.71B), community returns ($434M), jackpot frequency (17 Powerball struck, 64 millionaires created).
- **lotto.net** -- Historical Powerball jackpot results with draw dates and won amounts for 2025-2026.
- **Lotto NZ (mylotto.co.nz/about-lotto-nz/where-the-money-goes)** -- Cumulative community returns since 1987 ($5.9 billion plus).

---

## Methodology for Computed Series

### Published odds (Figure 1)

Lotto NZ uses a 6-from-40 ball draw with one bonus ball. The Powerball is drawn from a separate pool of 10. Strike uses the first 4 Lotto numbers drawn, in order.

- **Lotto Division 1**: C(40,6) = 3,838,380 combinations. Odds: 1 in 3,838,380.
- **Powerball Division 1**: C(40,6) x 10 = 38,383,800. Odds: 1 in 38,383,800.
- **Strike 4**: 40 x 39 x 38 x 37 = 2,193,360 permutations. Odds: 1 in 2,193,360.

All higher-division odds (Divisions 2 through 7) account for partial matches with or without the bonus ball. These are published by Lotto NZ and reproduced as given; the underlying combinatorial formulas are not re-derived here.

### Probability comparison (Figure 3)

**Unconditional probabilities** are simply 1 / odds_1_in for a single line.

**Participation-adjusted probabilities** (annual) are computed as:
  P(at least one win in N lines) = 1 - (1 - p)^N
  where p = 1 / 38,383,800 and N = lines_per_draw x 104 draws.

For 4 lines per draw (minimum Lotto ticket): N = 416, giving odds of 1 in 92,269.
For 10 lines per draw: N = 1,040, giving odds of 1 in 36,907.

**Market-level probabilities** reflect the empirical reality:
  -- Per-draw: P(at least one winner) = 1 - (1 - 1/38,383,800)^(2,500,000) = 6.3%, giving odds of 1 in 15.9.
  -- Per-year: Given ~17 Powerball jackpots struck across 104 draws (FY2024), the empirical frequency is 17/104 = 16.3%, giving odds of 1 in 6.1.

### Jackpot history (Figure 2)

The draw schedule follows Lotto NZ's standard 2 draws per week (Wednesdays and Saturdays). The CSV contains 150 draws from 1 January 2025 to 6 June 2026. Won amounts on key dates are verified against lotto.net results. Intermediate rollover amounts are estimated based on the typical jackpot growth rate of $1M to $3M per rollover draw.

The record-breaking $55.2M jackpot on 15 November 2025 (Draw 92) is documented as a 12-draw rollover chain starting from $4M on 8 October 2025.

### Key parameters

Sales data and community returns are from the Lotto NZ Integrated Report 2023/24 (the most recent annual report). The lotto_family_share of 84.4% covers Lotto, Powerball, and Strike sales. Estimated lines per draw (2.5M) is derived from average per-draw sales divided by typical line pricing, and is consistent with observed jackpot frequency.

---

## Reproducibility

- All odds data is sourced from mylotto.co.nz game information pages, accessed and verified on 20 July 2026.
- Sales and community returns data is from the publicly available Lotto NZ Integrated Report 2023/24.
- Jackpot won amounts are verified against lotto.net historical results. Rollover amounts between known won dates are author estimates intended to be representative, not exact.
- Charts.js contains the same data arrays plotted in each figure. The CSV values and charts.js arrays should match. If discrepancies are found, the CSV is the more recent compilation.
- Python or R users can reproduce the probability calculations using `scipy.stats` or the base `combinat` package, respectively.

---

## Disclaimer

This data package is a supplementary resource to the analytical brief. It is not a substitute for official Lotto NZ publications. Jackpot rollover amounts between verified won dates are author estimates. Users requiring exact draw-by-draw results should consult lotto.net or the official Lotto NZ results database. The author accepts no liability for errors in compilation or for decisions made based on this data.
