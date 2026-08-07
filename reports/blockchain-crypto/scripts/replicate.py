#!/usr/bin/env python3
"""
Replication script: Blockchain and Cryptocurrency in Business (2009-2026)
Author: Dr Yuqian Zhang
Date: 10 July 2026
Purpose: Reproduce all 11 figures and key statistics from the research brief
         using data in ../data/.
"""

# --- Dependencies (install with: pip install pandas numpy matplotlib --break-system-packages) ---
# pandas==2.2.0
# numpy==1.26.0
# matplotlib==3.8.0

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
import sys

# --- Reproducibility ---
np.random.seed(42)

# --- Paths ---
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "data"
CHARTS_DIR = SCRIPT_DIR.parent / "charts"
CHARTS_DIR.mkdir(exist_ok=True)

# --- Colour palette (matches report) ---
C_BLUE = "#1e3a5f"
C_RED = "#c0392b"
C_GREEN = "#059669"
C_AMBER = "#d97706"
C_PURPLE = "#7c3aed"
C_GREY = "#7f8c8d"
C_DARK_RED = "#922b21"
C_MID_BLUE = "#3b6e9e"
C_LIGHT_BLUE = "#7ba3cc"
C_PALE_BLUE = "#a4c8e8"
C_STABLECOIN_BLUE = "#2775ca"


def check_file(filepath):
    if not filepath.exists():
        print(f"ERROR: Required file not found: {filepath}")
        print(f"Expected location: {filepath}")
        sys.exit(1)
    return filepath


# ============================================================================
# Figure 1: Crypto Market Capitalisation and BTC Dominance (2013-2025)
# ============================================================================
print("Figure 1: Crypto Market Cap and BTC Dominance...")

mc = pd.read_csv(
    check_file(DATA_DIR / "crypto_market_cap.csv"),
    comment="#",
    dtype={"year": int, "total_market_cap_usd_billions": float,
           "btc_price_year_end": float, "btc_dominance_pct": float},
)

fig, ax1 = plt.subplots(figsize=(11, 6))
years = mc["year"].values
bars_data = mc["total_market_cap_usd_billions"].values
line_data = mc["btc_dominance_pct"].values

ax1.bar(years, bars_data, color=C_BLUE, width=0.7, zorder=2, label="Total Market Cap (USD B)")
ax1.set_xlabel("Year")
ax1.set_ylabel("USD B")
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:,.0f}B" if v < 1000 else f"${v/1000:.1f}T"))
ax1.set_xticks(years)

ax2 = ax1.twinx()
ax2.plot(years, line_data, color=C_AMBER, linewidth=2.5, marker="o", markersize=6,
         zorder=3, label="BTC Dominance (%)")
ax2.set_ylabel("%")
ax2.set_ylim(0, 100)
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=9)

ax1.set_title("Figure 1: Crypto Market Capitalisation and Bitcoin Dominance (2013-2025)", fontsize=13, fontweight="bold")
fig.tight_layout()
fig.savefig(CHARTS_DIR / "fig1_market_cap.png", dpi=150)
plt.close(fig)
print("  -> charts/fig1_market_cap.png")


# ============================================================================
# Figure 2: Major Crypto Exchange and Protocol Failure Losses (2014-2022)
# ============================================================================
print("Figure 2: Exchange/Protocol Failures...")

ef = pd.read_csv(
    check_file(DATA_DIR / "crypto_exchange_failures.csv"),
    comment="#",
    dtype={"estimated_loss_usd_billions": float},
)

ordered = ["Mt. Gox", "Terra/LUNA", "Three Arrows Capital (3AC)", "Celsius Network",
           "Voyager Digital", "FTX", "BlockFi", "Genesis Global Capital"]
ef["entity_sort"] = ef["entity"].apply(lambda x: ordered.index(x) if x in ordered else 99)
ef = ef.sort_values("entity_sort", ascending=False)

labels = ef["entity"].values
values = ef["estimated_loss_usd_billions"].values
colors_fail = [
    C_GREY, C_DARK_RED, C_AMBER, C_AMBER, C_AMBER, C_RED, C_BLUE, C_BLUE,
]

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.barh(labels, values, color=colors_fail[:len(labels)], height=0.6)
for bar, val in zip(bars, values):
    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
            f"${val:.1f}B", va="center", fontsize=9)
ax.set_xlabel("Est. Loss (USD Billions)")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:.0f}B"))
ax.set_title("Figure 2: Major Crypto Exchange and Protocol Failure Losses (2014-2022)", fontsize=13, fontweight="bold")
fig.tight_layout()
fig.savefig(CHARTS_DIR / "fig2_exchange_failures.png", dpi=150)
plt.close(fig)
print("  -> charts/fig2_exchange_failures.png")


# ============================================================================
# Figure 3: Bitcoin Year-End Price and Annual Range (2013-2025)
# ============================================================================
print("Figure 3: Bitcoin Price History...")

btc_high = [1150, 1163, 505, 982, 19783, 17148, 13796, 29370, 68789, 47927,
            44705, 106000, 126198]
btc_low = [13, 200, 150, 360, 770, 3122, 3322, 3850, 28993, 15479,
           16688, 38000, 82000]

fig, ax = plt.subplots(figsize=(10, 5.5))
ax.bar(years, mc["btc_price_year_end"].values, color=C_BLUE, width=0.6,
       zorder=2, label="Year-End Close")
ax.errorbar(years, mc["btc_price_year_end"].values,
            yerr=[mc["btc_price_year_end"].values - btc_low, np.array(btc_high) - mc["btc_price_year_end"].values],
            fmt="none", ecolor=C_RED, alpha=0.5, capsize=3, linewidth=1.5, zorder=3,
            label="Annual High-Low Range")
ax.scatter(years, btc_high, color=C_RED, s=15, zorder=4)
ax.scatter(years, btc_low, color=C_RED, s=15, zorder=4)
ax.set_xlabel("Year")
ax.set_ylabel("Price (USD)")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:,.0f}"))
ax.set_xticks(years)
ax.legend(fontsize=9)
ax.set_title("Figure 3: Bitcoin Year-End Price and Annual Range (2013-2025)", fontsize=13, fontweight="bold")
fig.tight_layout()
fig.savefig(CHARTS_DIR / "fig3_btc_price.png", dpi=150)
plt.close(fig)
print("  -> charts/fig3_btc_price.png")


# ============================================================================
# Figure 4: Spot Bitcoin ETF Cumulative Net Flows (Jan 2024 - 9 July 2026)
# ============================================================================
print("Figure 4: ETF Net Flows...")

etf = pd.read_csv(
    check_file(DATA_DIR / "crypto_etf_flows.csv"),
    comment="#",
    dtype={"cumulative_net_flows_usd_millions": float},
)
etf_data = etf.set_index("fund")["cumulative_net_flows_usd_millions"]

fund_order = ["iShares Bitcoin Trust", "Fidelity Wise Origin Bitcoin Fund",
              "Grayscale Bitcoin Mini Trust", "Bitwise Bitcoin ETF",
              "ARK 21Shares Bitcoin ETF", "VanEck Bitcoin ETF",
              "Other Bitcoin ETFs (combined)", "Grayscale Bitcoin Trust"]
short_names = ["iShares IBIT", "Fidelity FBTC", "Grayscale BTC Mini", "Bitwise BITB",
               "ARK 21Shares", "VanEck HODL", "Other ETFs", "GBTC (Grayscale)"]

plot_vals = [etf_data.get(f, 0) for f in fund_order]
colors_etf = [C_BLUE if v >= 0 else C_RED for v in plot_vals]

fig, ax = plt.subplots(figsize=(10, 4.5))
bars = ax.barh(short_names, plot_vals, color=colors_etf, height=0.6)
for bar, val in zip(bars, plot_vals):
    sign = "+" if val > 0 else ""
    ax.text(bar.get_width() + (0.5 if val >= 0 else -0.5),
            bar.get_y() + bar.get_height() / 2,
            f"{sign}${val/1000:.1f}B" if abs(val) >= 1000 else f"{sign}${val:.0f}M",
            va="center", fontsize=9,
            ha="left" if val >= 0 else "right")
ax.axvline(0, color="black", linewidth=0.8)
ax.set_xlabel("Cumulative Net Flows (USD Billions)")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v/1000:.1f}B"))
ax.set_title("Figure 4: Spot Bitcoin ETF Cumulative Net Flows (to 9 July 2026)", fontsize=13, fontweight="bold")
fig.tight_layout()
fig.savefig(CHARTS_DIR / "fig4_etf_flows.png", dpi=150)
plt.close(fig)
print("  -> charts/fig4_etf_flows.png")


# ============================================================================
# Figure 5: Corporate Bitcoin Treasury Holdings (Mid-2026)
# ============================================================================
print("Figure 5: Corporate Treasury...")

ct = pd.read_csv(
    check_file(DATA_DIR / "crypto_corporate_treasury.csv"),
    comment="#",
    dtype={"btc_holdings": float},
)
ct = ct.sort_values("btc_holdings")

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.barh(ct["company"].values, ct["btc_holdings"].values,
               color=[C_RED if c == "Tesla" else C_BLUE for c in ct["company"]],
               height=0.6)
for bar, val, lbl in zip(bars, ct["btc_holdings"].values, ct["btc_holdings"].values):
    ax.text(bar.get_width() + 1000, bar.get_y() + bar.get_height() / 2,
            f"{val:,.0f} BTC", va="center", fontsize=9)
ax.set_xlabel("BTC Holdings")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax.set_title("Figure 5: Corporate Bitcoin Treasury Holdings (Mid-2026)", fontsize=13, fontweight="bold")
fig.tight_layout()
fig.savefig(CHARTS_DIR / "fig5_corporate_treasury.png", dpi=150)
plt.close(fig)
print("  -> charts/fig5_corporate_treasury.png")


# ============================================================================
# Figure 6: Global Crypto Regulatory Milestones (2013-2026)
# ============================================================================
print("Figure 6: Regulatory Timeline...")

rt = pd.read_csv(
    check_file(DATA_DIR / "crypto_regulatory_timeline.csv"),
    comment="#",
)
rt["date_parsed"] = pd.to_datetime(rt["date"], errors="coerce")

timeline_events = [
    ("2013-12-05", "PBOC notice"), ("2015-06-24", "BitLicense"),
    ("2017-04-01", "Japan recognises BTC"), ("2017-09-04", "China ICO ban"),
    ("2019-06-15", "FATF Travel Rule"), ("2021-06-09", "El Salvador BTC"),
    ("2021-09-24", "China ban"), ("2023-04-20", "MiCA adopted"),
    ("2023-12-13", "FASB ASU 2023-08"), ("2024-01-10", "SEC spot BTC ETFs"),
    ("2024-05-23", "SEC spot ETH ETFs"), ("2024-12-30", "MiCA Full"),
    ("2025-07-15", "GENIUS Act"), ("2026-02-04", "UK Crypto Regs"),
    ("2026-04-01", "AUS Digital Assets"),
]
t_dates = [pd.Timestamp(d) for d, _ in timeline_events]
t_labels = [l for _, l in timeline_events]
t_colors = {
    "PBOC notice": C_DARK_RED, "BitLicense": "#2980b9", "Japan recognises BTC": "#27ae60",
    "China ICO ban": C_RED, "El Salvador BTC": "#f39c12", "China ban": C_RED,
    "FATF Travel Rule": C_GREY, "MiCA adopted": C_BLUE, "FASB ASU 2023-08": C_PURPLE,
    "SEC spot BTC ETFs": C_GREEN, "SEC spot ETH ETFs": C_GREEN, "MiCA Full": C_BLUE,
    "GENIUS Act": C_AMBER, "UK Crypto Regs": C_MID_BLUE, "AUS Digital Assets": C_MID_BLUE,
}

fig, ax = plt.subplots(figsize=(11, 5))
for i, (label, dt) in enumerate(zip(t_labels, t_dates)):
    ax.scatter(dt, i, s=80, color=t_colors.get(label, C_BLUE), zorder=3)
    ax.text(dt, i + 0.25, label, fontsize=8, ha="center", va="bottom",
            rotation=0, fontweight="bold")

ax.set_ylim(-1, len(t_labels) + 0.5)
ax.set_yticks(range(len(t_labels)))
ax.set_yticklabels(t_labels, fontsize=8)
ax.set_xlim(pd.Timestamp("2012-12-01"), pd.Timestamp("2026-07-01"))
ax.set_title("Figure 6: Global Crypto Regulatory Milestones (2013-2026)", fontsize=13, fontweight="bold")
ax.grid(axis="x", alpha=0.3)
fig.tight_layout()
fig.savefig(CHARTS_DIR / "fig6_regulatory.png", dpi=150)
plt.close(fig)
print("  -> charts/fig6_regulatory.png")


# ============================================================================
# Figure 7: CBDC Development Progress by Country (2018-2026)
# ============================================================================
print("Figure 7: CBDC Progress...")

cbdc = pd.read_csv(
    check_file(DATA_DIR / "crypto_cbdc_progress.csv"),
    comment="#",
    dtype={"countries_exploring": int, "countries_in_pilot": int, "countries_launched": int},
)

fig, ax = plt.subplots(figsize=(10, 5))
x = cbdc["year"].values
ax.bar(x, cbdc["countries_exploring"].values, color=C_PALE_BLUE, width=0.7, label="Exploring")
ax.bar(x, cbdc["countries_in_pilot"].values, bottom=cbdc["countries_exploring"].values,
       color=C_MID_BLUE, width=0.7, label="In Pilot")
ax.bar(x, cbdc["countries_launched"].values,
       bottom=cbdc["countries_exploring"].values + cbdc["countries_in_pilot"].values,
       color=C_BLUE, width=0.7, label="Launched")
ax.set_xlabel("Year")
ax.set_ylabel("Countries")
ax.set_xticks(x)
ax.legend(fontsize=9, loc="upper left")
ax.set_title("Figure 7: CBDC Development Progress by Country (2018-2026)", fontsize=13, fontweight="bold")
fig.tight_layout()
fig.savefig(CHARTS_DIR / "fig7_cbdc.png", dpi=150)
plt.close(fig)
print("  -> charts/fig7_cbdc.png")


# ============================================================================
# Figure 8: DeFi TVL and Stablecoin Market Cap (2019-2025)
# ============================================================================
print("Figure 8: DeFi TVL and Stablecoins...")

df_s = pd.read_csv(
    check_file(DATA_DIR / "crypto_defi_stablecoin_nft.csv"),
    comment="#",
    dtype={"defi_tvl_usd_billions": float, "stablecoin_mcap_usd_billions": float},
)
df_s = df_s[df_s["year"] >= 2019]

fig, ax1_8 = plt.subplots(figsize=(10, 5))
ax1_8.bar(df_s["year"].values, df_s["defi_tvl_usd_billions"].values,
          color=C_PURPLE, width=0.6, zorder=2, label="DeFi TVL")
ax1_8.set_xlabel("Year")
ax1_8.set_ylabel("USD Billions")
ax1_8.set_xticks(df_s["year"].values)

ax2_8 = ax1_8.twinx()
ax2_8.plot(df_s["year"].values, df_s["stablecoin_mcap_usd_billions"].values,
           color=C_GREEN, linewidth=2.5, marker="s", markersize=7, zorder=3,
           label="Stablecoin Mcap")
ax2_8.set_ylabel("USD Billions")

lines1_8, labels1_8 = ax1_8.get_legend_handles_labels()
lines2_8, labels2_8 = ax2_8.get_legend_handles_labels()
ax1_8.legend(lines1_8 + lines2_8, labels1_8 + labels2_8, loc="upper left", fontsize=9)
ax1_8.set_title("Figure 8: DeFi TVL and Stablecoin Market Cap (2019-2025)", fontsize=13, fontweight="bold")
fig.tight_layout()
fig.savefig(CHARTS_DIR / "fig8_defi_stablecoin.png", dpi=150)
plt.close(fig)
print("  -> charts/fig8_defi_stablecoin.png")


# ============================================================================
# Figure 9: Academic Literature Distribution (Journals and Themes)
# ============================================================================
print("Figure 9: Academic Literature...")

lit = pd.read_csv(
    check_file(DATA_DIR / "crypto_academic_literature.csv"),
    comment="#",
)

journal_counts = lit["journal"].value_counts().to_dict()
journals = ["Journal of Accounting Research", "Journal of Finance",
            "Journal of Financial Economics", "Review of Financial Studies",
            "Management Science", "Review of Accounting Studies"]
journal_abbr = ["JAR", "JF", "JFE", "RFS", "MS", "RAST"]
j_counts = [journal_counts.get(j, 0) for j in journals] + \
           [sum(v for k, v in journal_counts.items() if k not in journals)]

topics = {
    "Bitcoin/Markets": ["Easley", "Makarov", "Griffin", "Liu Y", "Pagnotta", "Biais", "Augustin", "Foley", "Hinzen"],
    "ICO/Token Financing": ["Howell", "Chod", "Gryglewicz", "Bourveau T", "Davydiuk", "Lyandres"],
    "Tokenomics": ["Cong LW; Li Y", "Malinova", "Sockin", "Cong LW; He"],
    "DeFi/Smart Contracts": ["Saleh", "Park A", "Cong LW; He"],
    "Stablecoins": ["Griffin"],
    "CBDC": ["Chiu"],
    "Accounting/Auditing": ["Bourveau T; Brendel", "Luo", "Anderson"],
    "Illegal Activity": ["Foley"],
}
t_counts = {k: len(v) for k, v in topics.items()}
t_key_order = ["Bitcoin/Markets", "ICO/Token Financing", "Tokenomics",
               "DeFi/Smart Contracts", "Stablecoins", "CBDC",
               "Accounting/Auditing", "Illegal Activity"]
t_vals = [t_counts.get(k, 0) for k in t_key_order]

all_labels = journal_abbr + ["Other"] + t_key_order
all_vals = j_counts + t_vals
all_colors = [C_BLUE] * len(journal_abbr + ["Other"]) + [C_PURPLE] * len(t_key_order)

fig, ax = plt.subplots(figsize=(10, 5.5))
bars = ax.barh(all_labels, all_vals, color=all_colors, height=0.6)
for bar, val in zip(bars, all_vals):
    ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
            str(val), va="center", fontsize=9)
ax.set_xlabel("Count")
ax.set_title("Figure 9: Academic Literature: Journal and Thematic Distribution", fontsize=13, fontweight="bold")
fig.tight_layout()
fig.savefig(CHARTS_DIR / "fig9_literature.png", dpi=150)
plt.close(fig)
print("  -> charts/fig9_literature.png")


# ============================================================================
# Figure 10: Stablecoin Market Capitalisation Growth (2020-2025)
# ============================================================================
print("Figure 10: Stablecoin Growth...")

sc_data = df_s.copy()
sc_data["other"] = sc_data["stablecoin_mcap_usd_billions"] - sc_data["usdt_mcap_usd_billions"] - sc_data["usdc_mcap_usd_billions"]
sc_data = sc_data[sc_data["year"] >= 2020]

fig, ax = plt.subplots(figsize=(10, 5))
years_sc = [2020, 2021, 2022, 2023, 2024, 2025]
usdt = [21, 78, 66, 91, 137, 184]
usdc = [4, 42, 44, 25, 44, 73]
other_sc = [0, 50, 29, 14, 24, 18]

ax.bar(years_sc, usdt, color=C_GREEN, width=0.6, label="USDT")
ax.bar(years_sc, usdc, bottom=usdt, color=C_STABLECOIN_BLUE, width=0.6, label="USDC")
ax.bar(years_sc, other_sc, bottom=[u + s for u, s in zip(usdt, usdc)],
       color=C_PALE_BLUE, width=0.6, label="Other")
ax.set_xlabel("Year")
ax.set_ylabel("USD Billions")
ax.set_xticks(years_sc)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:.0f}B"))
ax.legend(fontsize=9)
ax.set_title("Figure 10: Stablecoin Market Capitalisation Growth (2020-2025)", fontsize=13, fontweight="bold")
fig.tight_layout()
fig.savefig(CHARTS_DIR / "fig10_stablecoin_growth.png", dpi=150)
plt.close(fig)
print("  -> charts/fig10_stablecoin_growth.png")


# ============================================================================
# Figure 11: Research Opportunity Landscape
# ============================================================================
print("Figure 11: Research Opportunities...")

opp_data = [
    ("Crypto Accounting\n(FASB/IFRS)", 9, 9, 28),
    ("Corporate Treasury\nCrypto Holdings", 8, 8, 25),
    ("ETF Impact on\nMarket Quality", 8, 9, 22),
    ("Regulatory Effects\n(Diff-in-Diff)", 7, 8, 20),
    ("DeFi Governance\nand Tokens", 6, 7, 18),
    ("Stablecoin Payment\nInfrastructure", 6, 8, 16),
    ("Blockchain Audit\nand Assurance", 5, 6, 14),
    ("CBDC and Banking\nIntermediation", 5, 7, 12),
]

fig, ax = plt.subplots(figsize=(10, 6))
for label, dx, dy, sz in opp_data:
    ax.scatter(dx, dy, s=sz * 3, color=C_BLUE, alpha=0.75, edgecolors="white")
    ax.text(dx, dy + 0.4, label, fontsize=8, ha="center", va="bottom")
ax.set_xlabel("Data Availability", fontsize=10)
ax.set_ylabel("Theoretical Significance", fontsize=10)
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.set_title("Figure 11: Research Opportunity Landscape", fontsize=13, fontweight="bold")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(CHARTS_DIR / "fig11_research_opps.png", dpi=150)
plt.close(fig)
print("  -> charts/fig11_research_opps.png")


# ============================================================================
# Key Statistics Verification
# ============================================================================
print("\n" + "=" * 70)
print("KEY STATISTICS VERIFICATION")
print("=" * 70)

print(f"\nTotal market cap ATH (2025): ${mc['total_market_cap_usd_billions'].max():.1f}B")
print(f"  Confirmed: ATH $4.31T reached 6 October 2025 (CoinCodex)")
print(f"Market cap 2025 year-end: ${mc.iloc[-1]['total_market_cap_usd_billions']:.0f}B")
print(f"Bitcoin price 2025 year-end: ${mc.iloc[-1]['btc_price_year_end']:,.0f}")

strategy = ct[ct["company"].str.contains("Strategy")]
print(f"\nStrategy BTC holdings: {strategy['btc_holdings'].values[0]:,.0f} BTC")
print(f"  Cost basis: ${strategy['estimated_cost_basis_usd'].values[0]/1e9:.1f}B")
print(f"  Avg cost/BTC: ${strategy['avg_cost_per_btc_usd'].values[0]:,.0f}")

print(f"\nBTC ETF total net flows: ${etf_data.get('TOTAL', 0)/1000:.1f}B")
print(f"  iShares IBIT: ${etf_data.get('iShares Bitcoin Trust', 0)/1000:.1f}B")
print(f"  GBTC outflows: ${etf_data.get('Grayscale Bitcoin Trust', 0)/1000:.1f}B")

cbdc_2026 = cbdc[cbdc["year"] == 2026].iloc[0]
print(f"\nCBDCs exploring (2026): {cbdc_2026['countries_exploring']} countries")
print(f"  In pilot: {cbdc_2026['countries_in_pilot']}, Launched: {cbdc_2026['countries_launched']}")

sc_2025 = df_s[df_s["year"] == 2025].iloc[0]
print(f"\nStablecoin market cap (2025): ${sc_2025['stablecoin_mcap_usd_billions']:.0f}B")
print(f"  USDT: ${sc_2025['usdt_mcap_usd_billions']:.0f}B")
print(f"  USDC: ${sc_2025['usdc_mcap_usd_billions']:.0f}B")

fail_total = ef["estimated_loss_usd_billions"].sum()
print(f"\nTotal exchange/protocol failure losses: ${fail_total:.1f}B")

print(f"\nAcademic papers in literature review: {len(lit)}")
print(f"  Journals represented: {lit['journal'].nunique()}")
print("=" * 70)
print(f"\nAll 11 charts saved to {CHARTS_DIR}/")
print("Replication complete.")
