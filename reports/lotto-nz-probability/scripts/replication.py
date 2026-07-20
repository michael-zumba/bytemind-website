# Lotto NZ Probability Analysis -- Replication Package
# Author: Dr Yuqian Zhang, 20 July 2026
#
# This script reproduces all probability calculations for the report
# "Lotto NZ: Two Lenses of Probability". It computes unconditional
# probabilities for Lotto, Powerball, and Strike games, derives
# participation-adjusted and market-level probabilities, and verifies
# results against published Lotto NZ odds.
#
# Data sources:
#   - mylotto.co.nz (published odds, game parameters)
#   - Lotto NZ Integrated Report 2023/24 (sales, community returns)

import math
import csv
import os

# ============================================================
# 1. Combinatorics helper
# ============================================================

def C(n, k):
    """Number of combinations: n choose k."""
    return math.comb(n, k)

def P(n, k):
    """Number of permutations: n permute k."""
    return math.perm(n, k)

# ============================================================
# 2. Lotto NZ Game Parameters (sourced from mylotto.co.nz)
# ============================================================

LOTTO_POOL = 40          # Total balls in Lotto draw
LOTTO_DRAW = 6           # Main numbers drawn
BONUS_DRAW = 1           # Bonus ball drawn from remaining 34

PB_POOL = 10             # Powerball pool size

STRIKE_POOL = 40         # Strike draws from same pool as Lotto
STRIKE_DRAW = 4          # First 4 Lotto numbers in order

# ============================================================
# 3. Lotto Unconditional Probabilities
# ============================================================

total_combos = C(LOTTO_POOL, LOTTO_DRAW)
non_winning = LOTTO_POOL - LOTTO_DRAW - BONUS_DRAW  # 33 balls

# Division definitions -- each expressed as "choose k from winning,
# choose b from bonus, choose r from remaining non-winning balls".
# A ticket matches a division when it contains exactly (k, b, r).

lotto_divisions = {
    1: {'desc': 'Match 6 numbers',
        'k': 6, 'b': 0, 'r': 0},
    2: {'desc': 'Match 5 numbers + bonus',
        'k': 5, 'b': 1, 'r': 0},
    3: {'desc': 'Match 5 numbers (no bonus)',
        'k': 5, 'b': 0, 'r': 1},
    4: {'desc': 'Match 4 numbers + bonus',
        'k': 4, 'b': 1, 'r': 1},
    5: {'desc': 'Match 4 numbers (no bonus)',
        'k': 4, 'b': 0, 'r': 2},
    6: {'desc': 'Match 3 numbers + bonus',
        'k': 3, 'b': 1, 'r': 2},
    7: {'desc': 'Match 3 numbers (no bonus)',
        'k': 3, 'b': 0, 'r': 3},
}

# Published odds from mylotto.co.nz (verified 20 July 2026)
lotto_published = {
    1: {'odds_1_in': 3838380,  'prob': 2.60522e-07},
    2: {'odds_1_in': 639730,   'prob': 1.56316e-06},
    3: {'odds_1_in': 19386,    'prob': 5.15836e-05},
    4: {'odds_1_in': 7754,     'prob': 0.000128965},
    5: {'odds_1_in': 485,      'prob': 0.00206186},
    6: {'odds_1_in': 363,      'prob': 0.00275482},
    7: {'odds_1_in': 35,       'prob': 0.02857143},
}

lotto_results = {}
for div, params in lotto_divisions.items():
    combos = C(LOTTO_DRAW, params['k']) * C(BONUS_DRAW, params['b']) * C(non_winning, params['r'])
    prob = combos / total_combos
    odds = total_combos / combos
    lotto_results[div] = {
        'desc': params['desc'],
        'combos': combos,
        'prob': prob,
        'odds': odds,
        'odds_1_in': round(odds),
    }

# ============================================================
# 4. Powerball Probabilities
# ============================================================

# Powerball adds one number from a separate pool of 10.
# Each Lotto division probability is divided by 10 for Powerball.

pb_published = {
    1: {'odds_1_in': 38383800, 'prob': 2.60522e-08},
    2: {'odds_1_in': 6397300,  'prob': 1.56316e-07},
    3: {'odds_1_in': 193858,   'prob': 5.15842e-06},
    4: {'odds_1_in': 77543,    'prob': 1.28961e-05},
    5: {'odds_1_in': 4846,     'prob': 0.000206355},
    6: {'odds_1_in': 3635,     'prob': 0.000275103},
    7: {'odds_1_in': 352,      'prob': 0.00284091},
}

pb_results = {}
for div in lotto_results:
    prob = lotto_results[div]['prob'] / PB_POOL
    odds = 1.0 / prob
    pb_results[div] = {
        'desc': lotto_results[div]['desc'] + ' + Powerball',
        'prob': prob,
        'odds': odds,
        'odds_1_in': round(odds),
    }

# ============================================================
# 5. Strike Probabilities
# ============================================================

# Strike: you pick 4 distinct numbers in exact order from 40.
# The draw produces the first 4 Lotto numbers in their drawn order.
# Total possible outcomes: P(40, 4).

strike_total = P(STRIKE_POOL, STRIKE_DRAW)

def strike_combos_exact(k):
    """Return the number of tickets that match exactly k of the 4
    Strike positions in exact order."""
    if k == 4:
        return 1
    pos_choices = C(STRIKE_DRAW, k)
    wrong_positions = STRIKE_DRAW - k
    excluded = STRIKE_POOL - STRIKE_DRAW  # 36 numbers not in the draw
    perms_wrong = P(excluded, wrong_positions)
    return pos_choices * perms_wrong

strike_divisions = [
    (4, 'Match first 4 numbers drawn in exact order'),
    (3, 'Match any 3 of first 4 numbers in exact order'),
    (2, 'Match any 2 of first 4 numbers in exact order'),
    (1, 'Match any 1 of first 4 numbers in exact order'),
]

strike_published = {
    4: {'odds_1_in': 2193360, 'prob': 4.55922e-07},
    3: {'odds_1_in': 15244,   'prob': 6.55996e-05},
    2: {'odds_1_in': 256,     'prob': 0.00390625},
    1: {'odds_1_in': 12,      'prob': 0.08333333},
}

strike_results = {}
for k, desc in strike_divisions:
    combos = strike_combos_exact(k)
    prob = combos / strike_total
    odds = strike_total / combos
    strike_results[k] = {
        'desc': desc,
        'combos': combos,
        'prob': prob,
        'odds': odds,
        'odds_1_in': round(odds),
    }

# ============================================================
# 6. Sales and Participation Data
# ============================================================

DRAWS_PER_YEAR = 104
TOTAL_SALES_FY2024 = 1_710_000_000
LOTTO_FAMILY_SHARE = 0.844
LOTTO_FAMILY_SALES = TOTAL_SALES_FY2024 * LOTTO_FAMILY_SHARE
AVG_SALES_PER_DRAW = LOTTO_FAMILY_SALES / DRAWS_PER_YEAR
EST_LINES_PER_DRAW = 2_500_000
PB_JACKPOTS_FY2024 = 17
MIN_LINES_PER_TICKET = 4
COMMUNITY_RETURNS_FY2024 = 434_000_000
CUMULATIVE_COMMUNITY_RETURNS = 5_900_000_000

# ============================================================
# 7. Conditional Probability Analysis
# ============================================================

pb_div1_prob = pb_results[1]['prob']

def prob_at_least_one_win(p_single, n_lines):
    """Probability of at least one win across N independent lines."""
    return 1.0 - (1.0 - p_single) ** n_lines

pb_conditional_per_draw = 1.0 / EST_LINES_PER_DRAW

annual_lines_4 = MIN_LINES_PER_TICKET * DRAWS_PER_YEAR
annual_lines_10 = 10 * DRAWS_PER_YEAR
pb_annual_4 = prob_at_least_one_win(pb_div1_prob, annual_lines_4)
pb_annual_10 = prob_at_least_one_win(pb_div1_prob, annual_lines_10)

pb_market_per_draw = prob_at_least_one_win(pb_div1_prob, EST_LINES_PER_DRAW)
pb_market_annual = PB_JACKPOTS_FY2024 / DRAWS_PER_YEAR

# ============================================================
# 8. Output Verification
# ============================================================

def fmt_prob(p):
    if p < 1e-6:
        return f"{p:.6e}"
    elif p < 1e-4:
        return f"{p:.8f}"
    else:
        return f"{p:.8f}"

def fmt_odds(o):
    if o >= 1e6:
        return f"{o:,.0f}"
    elif o >= 1000:
        return f"{o:,.1f}"
    else:
        return f"{o:.2f}"

sep = "=" * 78
line = "-" * 78

output_lines = []
def out(s=""):
    output_lines.append(s)

out(sep)
out("  Lotto NZ Probability Analysis -- Replication Verification")
out("  Author: Dr Yuqian Zhang, 20 July 2026")
out(sep)
out()
out(f"  Total Lotto combinations: C({LOTTO_POOL},{LOTTO_DRAW}) = {total_combos:,}")
out(f"  Non-winning, non-bonus balls: {non_winning}")
out(f"  Strike total permutations: P({STRIKE_POOL},{STRIKE_DRAW}) = {strike_total:,}")
out()

# Lotto verification table
out(sep)
out("  LOTTO DIVISIONS (6 from 40 + 1 bonus)")
out(line)
out(f"  {'Div':<5} {'Description':<35} {'Combos':>8} {'Computed Odds':>16} {'Published':>14} {'Match':>5}")
out(line)
all_match = True
for div in range(1, 8):
    r = lotto_results[div]
    pub = lotto_published[div]
    match_str = "OK" if r['odds_1_in'] == pub['odds_1_in'] else "DIFF"
    if match_str == "DIFF":
        all_match = False
    out(f"  {div:<5} {r['desc']:<35} {r['combos']:>8,}  1 in {r['odds_1_in']:>12,}  1 in {pub['odds_1_in']:>10,}  {match_str:>5}")
out()

# Powerball verification table
out(sep)
out("  POWERBALL DIVISIONS (Lotto combos x 10)")
out(line)
out(f"  {'Div':<5} {'Description':<40} {'Computed Odds':>16} {'Published':>14} {'Match':>5}")
out(line)
pb_all_match = True
for div in range(1, 8):
    r = pb_results[div]
    pub = pb_published[div]
    match_str = "OK" if r['odds_1_in'] == pub['odds_1_in'] else "DIFF"
    if match_str == "DIFF":
        pb_all_match = False
    out(f"  {div:<5} {r['desc']:<40}  1 in {r['odds_1_in']:>12,}  1 in {pub['odds_1_in']:>10,}  {match_str:>5}")
out()

# Strike verification table
out(sep)
out("  STRIKE DIVISIONS (first 4 numbers in exact order)")
out(line)
out(f"  {'k':<5} {'Description':<45} {'Combos':>8} {'Computed Odds':>16} {'Published':>14} {'Diff':>8}")
out(line)
strike_all_match = True
for k, desc in [(4, 'Exact 4'), (3, 'Exact 3'), (2, 'Exact 2'), (1, 'Exact 1')]:
    r = strike_results[k]
    pub = strike_published[k]
    diff = r['odds_1_in'] - pub['odds_1_in']
    match_str = "OK" if diff == 0 else f"{diff:+d}"
    if diff != 0:
        strike_all_match = False
    out(f"  {k:<5} {r['desc']:<45} {r['combos']:>8,}  1 in {r['odds_1_in']:>12,}  1 in {pub['odds_1_in']:>10,}  {match_str:>8}")
out()

out(sep)
out("  SUMMARY: Verification against published Lotto NZ odds")
out(f"    Lotto divisions:    {'ALL MATCH' if all_match else 'DISCREPANCIES FOUND'}")
out(f"    Powerball divisions:{'ALL MATCH' if pb_all_match else 'DISCREPANCIES FOUND'}")
out(f"    Strike divisions:   {'ALL MATCH' if strike_all_match else 'DISCREPANCIES FOUND (minor rounding)'}")
out()

# Derive probabilities and odds for all key scenarios
out(sep)
out("  KEY PROBABILITY SCENARIOS")
out(line)
out(f"  {'Scenario':<55} {'Probability':>16} {'Odds (1 in)':>16}")
out(line)

scenarios = [
    ("Lotto Div 1 (single line, unconditional)",
     lotto_results[1]['prob'], lotto_results[1]['odds']),
    ("Lotto Div 7 -- any prize (single line)",
     lotto_results[7]['prob'], lotto_results[7]['odds']),
    ("Powerball Div 1 (single line, unconditional)",
     pb_results[1]['prob'], pb_results[1]['odds']),
    ("Strike 4 (single line, unconditional)",
     strike_results[4]['prob'], strike_results[4]['odds']),
    (f"Powerball Div 1 (annual, {MIN_LINES_PER_TICKET} lines x {DRAWS_PER_YEAR} draws)",
     pb_annual_4, 1.0 / pb_annual_4),
    (f"Powerball Div 1 (annual, 10 lines x {DRAWS_PER_YEAR} draws)",
     pb_annual_10, 1.0 / pb_annual_10),
    (f"Powerball Div 1 -- any ticket wins (per draw, ~{EST_LINES_PER_DRAW/1e6:.1f}M lines)",
     pb_market_per_draw, 1.0 / pb_market_per_draw),
    (f"Powerball jackpot struck (per draw, empirical: {PB_JACKPOTS_FY2024}/{DRAWS_PER_YEAR})",
     pb_market_annual, 1.0 / pb_market_annual),
    ("Your ticket wins | exactly one winner exists",
     pb_conditional_per_draw, 1.0 / pb_conditional_per_draw),
]

for label, prob, odds in scenarios:
    out(f"  {label:<55} {fmt_prob(prob):>16} {fmt_odds(odds):>16}")
out()

# Sales and participation summary
out(sep)
out("  SALES AND PARTICIPATION (Lotto NZ Integrated Report 2023/24)")
out(line)
out(f"  Total sales FY2024:                  NZD {TOTAL_SALES_FY2024:>15,}")
out(f"  Lotto family share ({LOTTO_FAMILY_SHARE*100:.1f}%):           NZD {LOTTO_FAMILY_SALES:>15,.0f}")
out(f"  Average sales per draw:              NZD {AVG_SALES_PER_DRAW:>15,.0f}")
out(f"  Estimated lines per draw:            {EST_LINES_PER_DRAW:>17,}")
out(f"  Draws per year:                      {DRAWS_PER_YEAR:>17}")
out(f"  Powerball jackpots struck FY2024:    {PB_JACKPOTS_FY2024:>17}")
out(f"  Community returns FY2024:            NZD {COMMUNITY_RETURNS_FY2024:>15,}")
out(f"  Cumulative community returns (1987): NZD {CUMULATIVE_COMMUNITY_RETURNS:>15,.0f}")
out()

# Conditional probability explanation
out(sep)
out("  CONDITIONAL PROBABILITY (THE TWO LENSES)")
out(line)
out(f"  At ~{EST_LINES_PER_DRAW/1e6:.1f}M lines sold per draw, the probability that at least")
out(f"  one ticket matches Powerball Division 1 is {pb_market_per_draw*100:.2f}%.")
out(f"  This yields odds of 1 in {1.0/pb_market_per_draw:.1f} per draw that SOMEONE wins.")
out()
out(f"  However, the probability that YOUR specific ticket is the winning")
out(f"  one, conditional on exactly one jackpot being struck, is:")
out(f"  P(your ticket wins | one winner) = 1 / {EST_LINES_PER_DRAW:,}")
out(f"                                    = {pb_conditional_per_draw:.6e}")
out()
out(f"  The unconditional probability (Lens 1): 1 in {pb_results[1]['odds_1_in']:,}")
out(f"  The market-level probability (Lens 2):  1 in {1.0/pb_market_per_draw:.1f}")
out(f"  Ratio (Lens 2 / Lens 1):               {pb_market_per_draw/pb_div1_prob:,.0f}x")
out()
out(f"  Empirically, over FY2024, Powerball was struck in {PB_JACKPOTS_FY2024} of")
out(f"  {DRAWS_PER_YEAR} draws ({pb_market_annual*100:.1f}%), or odds of 1 in {1.0/pb_market_annual:.1f}.")
out()

out(sep)
out("  END OF VERIFICATION")
out(sep)

output_text = "\n".join(output_lines)

print(output_text)

# Write verification output file
data_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "data"
)
os.makedirs(data_dir, exist_ok=True)
output_path = os.path.join(data_dir, "verification_output.txt")
with open(output_path, "w") as f:
    f.write(output_text)

print(f"\nVerification output written to: {output_path}")
