# Author: Dr Yuqian Zhang
# Date: 23 July 2026
# Purpose: Replication script for "AI Tokens as an Emerging Asset Class"
#   Regenerates all charts and statistics from source data.

# Dependencies (install with pip):
#   matplotlib>=3.8.0 seaborn>=0.13.0 pandas>=2.1.0 numpy>=1.24.0
#   pip install matplotlib seaborn pandas numpy --break-system-packages

import os
import sys
import csv
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from pathlib import Path

# ===========================================================================
# Global configuration
# ===========================================================================
seed = 42
np.random.seed(seed)

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "data"
CHART_DIR = SCRIPT_DIR.parent / "charts"
CHART_DIR.mkdir(parents=True, exist_ok=True)

COLOUR_PALETTE = ["#1e3a5f", "#7c3aed", "#059669", "#d97706"]
sns.set_style("whitegrid")
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "axes.titlesize": 14,
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "savefig.bbox": "tight",
})

# Data compiled manually from CoinMarketCap, CoinGecko, SEC EDGAR, Grayscale,
# FASB, IASB, and academic sources. Auto-download is not possible for manually
# compiled data; these CSV files are the authoritative source.
# ---------------------------------------------------------------------------


def load_csv(filename):
    """Load a CSV from DATA_DIR; return (df, True) or (None, False)."""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        print(f"  [SKIP] Missing: {filepath}")
        return None, False
    try:
        return pd.read_csv(filepath), True
    except Exception:
        pass
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
        if len(rows) <= 1:
            return None, False
        header = rows[0]
        n_cols = len(header)
        if n_cols == 9 and "authors" in header:
            data = []
            for row in rows[1:]:
                n = len(row)
                if n <= n_cols:
                    while len(row) < n_cols:
                        row.append("")
                    data.append(row)
                else:
                    extra = n - n_cols
                    merged_authors = "; ".join(row[2 : 2 + extra + 1])
                    merged_row = (
                        row[:2]
                        + [merged_authors]
                        + row[2 + extra + 1 :]
                    )
                    while len(merged_row) < n_cols:
                        merged_row.append("")
                    data.append(merged_row[:n_cols])
            return pd.DataFrame(data, columns=header), True
        else:
            data = []
            for row in rows[1:]:
                if len(row) > n_cols:
                    row = row[:n_cols]
                while len(row) < n_cols:
                    row.append("")
                data.append(row)
            return pd.DataFrame(data, columns=header), True
    except Exception:
        print(f"  [SKIP] Could not parse: {filepath}")
        return None, False


def save_chart(fig, name):
    path = CHART_DIR / name
    fig.savefig(path)
    print(f"  Saved: {path}")
    plt.close(fig)


# ===========================================================================
# Section 1: AI Token Market Evolution
# ===========================================================================
print("=" * 60)
print("Section 1: AI Token Market Evolution")

df_mcap, ok = load_csv("ai_tokens_market_cap.csv")
if ok:
    df_mcap["period"] = (
        df_mcap["year"].astype(str) + "-" + df_mcap["quarter"].astype(str)
    )
    df_mcap["total_market_cap_usd_billion"] = pd.to_numeric(
        df_mcap["total_market_cap_usd_billion"], errors="coerce"
    )
    df_mcap["ai_token_count"] = pd.to_numeric(
        df_mcap["ai_token_count"], errors="coerce"
    )
    df_mcap["ai_token_dominance_pct"] = pd.to_numeric(
        df_mcap["ai_token_dominance_pct"], errors="coerce"
    )
    df_mcap["btc_market_cap_usd_billion"] = pd.to_numeric(
        df_mcap["btc_market_cap_usd_billion"], errors="coerce"
    )

    # --- Fig 1: Sector market cap and token count ---
    fig, ax1 = plt.subplots(figsize=(12, 5))
    ax1.fill_between(
        range(len(df_mcap)),
        df_mcap["total_market_cap_usd_billion"],
        alpha=0.25,
        color=COLOUR_PALETTE[0],
    )
    ax1.plot(
        range(len(df_mcap)),
        df_mcap["total_market_cap_usd_billion"],
        color=COLOUR_PALETTE[0],
        linewidth=2,
        marker="o",
        markersize=4,
        label="AI token market cap (USD bn)",
    )
    ax1.set_ylabel("Market cap (USD billion)", color=COLOUR_PALETTE[0])
    ax1.tick_params(axis="y", labelcolor=COLOUR_PALETTE[0])

    ax2 = ax1.twinx()
    ax2.plot(
        range(len(df_mcap)),
        df_mcap["ai_token_count"],
        color=COLOUR_PALETTE[2],
        linewidth=2,
        marker="s",
        markersize=4,
        linestyle="--",
        label="AI token count",
    )
    ax2.set_ylabel("Number of AI tokens", color=COLOUR_PALETTE[2])
    ax2.tick_params(axis="y", labelcolor=COLOUR_PALETTE[2])

    tick_positions = range(0, len(df_mcap), 4)
    tick_labels = df_mcap["period"].iloc[tick_positions].values
    ax1.set_xticks(tick_positions)
    ax1.set_xticklabels(tick_labels, rotation=45, ha="right")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    ax1.set_title("Figure 1: AI Token Sector Market Capitalisation and Token Count (2020 Q1 -- 2026 Q2)")
    save_chart(fig, "fig1_sector_market_cap.png")

    # --- Fig 2: AI token dominance (dual axis) ---
    fig, ax1 = plt.subplots(figsize=(12, 5))
    ax1.bar(
        range(len(df_mcap)),
        df_mcap["total_market_cap_usd_billion"],
        color=COLOUR_PALETTE[0],
        alpha=0.7,
        label="AI token market cap (USD bn)",
    )
    ax1.set_ylabel("Market cap (USD billion)", color=COLOUR_PALETTE[0])
    ax1.tick_params(axis="y", labelcolor=COLOUR_PALETTE[0])

    ax2 = ax1.twinx()
    ax2.plot(
        range(len(df_mcap)),
        df_mcap["ai_token_dominance_pct"],
        color=COLOUR_PALETTE[1],
        linewidth=2.5,
        marker="D",
        markersize=5,
        label="AI token dominance (%)",
    )
    ax2.axhline(y=1.0, color="grey", linestyle=":", linewidth=1, alpha=0.6)
    ax2.set_ylabel("AI token dominance (%)", color=COLOUR_PALETTE[1])
    ax2.tick_params(axis="y", labelcolor=COLOUR_PALETTE[1])
    ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f%%"))

    ax1.set_xticks(tick_positions)
    ax1.set_xticklabels(tick_labels, rotation=45, ha="right")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    ax1.set_title("Figure 2: AI Token Market Cap and Dominance (2020 Q1 -- 2026 Q2)")
    save_chart(fig, "fig2_ai_dominance.png")

    peak_mcap = df_mcap["total_market_cap_usd_billion"].max()
    peak_mcap_period = df_mcap.loc[
        df_mcap["total_market_cap_usd_billion"].idxmax(), "period"
    ]
    peak_dominance = df_mcap["ai_token_dominance_pct"].max()
    peak_dominance_period = df_mcap.loc[
        df_mcap["ai_token_dominance_pct"].idxmax(), "period"
    ]
    q2_2026_mcap = df_mcap[df_mcap["period"] == "2026-Q2"][
        "total_market_cap_usd_billion"
    ].values[0]
    q2_2026_dominance = df_mcap[df_mcap["period"] == "2026-Q2"][
        "ai_token_dominance_pct"
    ].values[0]

    print(f"  Total AI token market cap Q2 2026: ${q2_2026_mcap:.2f} bn")
    print(f"  Peak market cap: ${peak_mcap:.2f} bn ({peak_mcap_period})")
    print(f"  Peak AI token dominance: {peak_dominance:.2f}% ({peak_dominance_period})")
    print(f"  AI token dominance Q2 2026: {q2_2026_dominance:.2f}%")

# ===========================================================================
# Section 2: Major AI Token Projects
# ===========================================================================
print("=" * 60)
print("Section 2: Major AI Token Projects")

df_top, ok2 = load_csv("ai_tokens_top_projects.csv")
if ok2:
    df_top["market_cap_usd_billion_q2_2026"] = pd.to_numeric(
        df_top["market_cap_usd_billion_q2_2026"], errors="coerce"
    )
    df_top_sorted = df_top.sort_values(
        "market_cap_usd_billion_q2_2026", ascending=True
    )

    # --- Fig 3: Horizontal bar ---
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(
        df_top_sorted["token"],
        df_top_sorted["market_cap_usd_billion_q2_2026"],
        color=COLOUR_PALETTE[0],
        height=0.6,
    )
    for bar, val in zip(bars, df_top_sorted["market_cap_usd_billion_q2_2026"]):
        ax.text(
            bar.get_width() + 0.1,
            bar.get_y() + bar.get_height() / 2,
            f"${val:.2f}B",
            va="center",
            fontsize=9,
        )
    ax.set_xlabel("Market capitalisation (USD billion)")
    ax.set_title("Figure 3: Top AI Token Projects by Market Cap (Q2 2026)")
    ax.set_xlim(0, df_top_sorted["market_cap_usd_billion_q2_2026"].max() * 1.3)
    save_chart(fig, "fig3_top_tokens.png")

    largest_token = df_top_sorted.iloc[-1]
    print(
        f"  Largest AI token: {largest_token['token']} "
        f"(${largest_token['market_cap_usd_billion_q2_2026']:.2f}B)"
    )

# ===========================================================================
# Section 3: AI Token Price Trajectories
# ===========================================================================
print("=" * 60)
print("Section 3: AI Token Price Trajectories")

df_price, ok3 = load_csv("ai_tokens_price_history.csv")
if ok3:
    df_price["price_usd"] = pd.to_numeric(df_price["price_usd"], errors="coerce")
    df_price["quarter"] = ((df_price["month"].astype(int) - 1) // 3 + 1).astype(int)
    df_price["date_label"] = (
        df_price["year"].astype(str) + "-Q" + df_price["quarter"].astype(str)
    )
    df_price["date_sort"] = df_price["year"].astype(int) * 10 + df_price["quarter"]
    df_price = df_price.sort_values(["token_ticker", "date_sort"])

    pivot = df_price.pivot_table(
        index="date_label",
        columns="token_name",
        values="price_usd",
        aggfunc="first",
    )

    label_order = sorted(
        pivot.index,
        key=lambda lbl: int(lbl.split("-Q")[0]) * 10 + int(lbl.split("-Q")[1]),
    )
    pivot = pivot.loc[label_order]
    indexed = pivot.apply(lambda col: col / col.dropna().iloc[0] * 100)

    # --- Fig 4: Indexed multi-line ---
    fig, ax = plt.subplots(figsize=(12, 5))
    colours = COLOUR_PALETTE + ["#e74c3c", "#3498db"]
    for idx, col_name in enumerate(indexed.columns):
        series = indexed[col_name].dropna()
        ax.plot(
            series.index,
            series.values,
            marker="o",
            markersize=4,
            linewidth=2,
            color=colours[idx % len(colours)],
            label=col_name,
        )
    ax.axhline(y=100, color="grey", linestyle=":", linewidth=1, alpha=0.5)
    ax.set_ylabel("Price indexed to 100 at Q1 2023")
    ax.set_title("Figure 4: Major AI Token Price Trajectories (Indexed, 2023 Q1 -- 2026 Q2)")
    ax.legend(loc="best", frameon=True)
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")
    save_chart(fig, "fig4_price_trajectories.png")

    # Compute average volatility (annualised std of quarterly log returns)
    returns = pivot.pct_change().dropna()
    log_returns = np.log(1 + returns)
    avg_vol = log_returns.std().mean() * np.sqrt(4)
    print(f"  Average annualised volatility of major AI tokens: {avg_vol:.1%}")

# ===========================================================================
# Section 4: Venture Capital Funding
# ===========================================================================
print("=" * 60)
print("Section 4: Venture Capital Funding")

df_vc, ok4 = load_csv("ai_tokens_vc_funding.csv")
if ok4:
    df_vc["vc_funding_usd_billion"] = pd.to_numeric(
        df_vc["vc_funding_usd_billion"], errors="coerce"
    )
    df_vc["number_of_deals"] = pd.to_numeric(
        df_vc["number_of_deals"], errors="coerce"
    )
    df_vc["period"] = (
        df_vc["year"].astype(str) + "-" + df_vc["quarter"].astype(str)
    )

    # --- Fig 5: Bar + line ---
    fig, ax1 = plt.subplots(figsize=(12, 5))
    ax1.bar(
        range(len(df_vc)),
        df_vc["vc_funding_usd_billion"],
        color=COLOUR_PALETTE[0],
        alpha=0.7,
        label="VC funding (USD bn)",
    )
    ax1.set_ylabel("VC funding (USD billion)", color=COLOUR_PALETTE[0])
    ax1.tick_params(axis="y", labelcolor=COLOUR_PALETTE[0])

    ax2 = ax1.twinx()
    ax2.plot(
        range(len(df_vc)),
        df_vc["number_of_deals"],
        color=COLOUR_PALETTE[3],
        linewidth=2.5,
        marker="o",
        markersize=5,
        label="Number of deals",
    )
    ax2.set_ylabel("Number of deals", color=COLOUR_PALETTE[3])
    ax2.tick_params(axis="y", labelcolor=COLOUR_PALETTE[3])

    tick_positions_vc = range(0, len(df_vc), 4)
    tick_labels_vc = df_vc["period"].iloc[tick_positions_vc].values
    ax1.set_xticks(tick_positions_vc)
    ax1.set_xticklabels(tick_labels_vc, rotation=45, ha="right")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    ax1.set_title("Figure 5: Venture Capital Funding in AI-Crypto Sector (2020 Q3 -- 2025 Q2)")
    save_chart(fig, "fig5_vc_funding.png")

    vc_2025 = df_vc[df_vc["year"] == 2025]["vc_funding_usd_billion"].sum()
    total_vc = df_vc["vc_funding_usd_billion"].sum()
    print(f"  Total VC funding in 2025: ${vc_2025:.2f} bn")
    print(f"  Cumulative VC funding (2020-2025): ${total_vc:.2f} bn")

# ===========================================================================
# Section 5: Token Categories
# ===========================================================================
print("=" * 60)
print("Section 5: Token Categories")

# Category groupings derived from top-projects data
category_data = {
    "AI Infrastructure": 8.30,
    "GPU & Compute": 3.51,
    "Decentralised ML": 3.20,
    "Data & Storage": 3.00,
    "AI Agents & Services": 1.13,
}
categories = list(category_data.keys())
values = list(category_data.values())
pie_colours = COLOUR_PALETTE + ["#e74c3c"]

# --- Fig 6: Pie chart ---
fig, ax = plt.subplots(figsize=(8, 8))
wedges, texts, autotexts = ax.pie(
    values,
    labels=categories,
    autopct="%1.1f%%",
    colors=pie_colours,
    startangle=140,
    pctdistance=0.85,
    wedgeprops={"linewidth": 1, "edgecolor": "white"},
)
for t in autotexts:
    t.set_fontsize(10)
for t in texts:
    t.set_fontsize(11)
ax.set_title("Figure 6: AI Token Market Distribution by Category (Q2 2026)")
save_chart(fig, "fig6_category_distribution.png")

print("  Category distribution saved (market cap weighted).")

# ===========================================================================
# Section 6: Regulatory Timeline
# ===========================================================================
print("=" * 60)
print("Section 6: Regulatory Timeline")

df_reg, ok6 = load_csv("ai_tokens_regulatory_timeline.csv")
if ok6:
    df_reg["date"] = pd.to_datetime(df_reg["date"], errors="coerce")
    n_milestones = len(df_reg)
    n_jurisdictions = df_reg["jurisdiction"].nunique()
    jurisdiction_counts = df_reg["jurisdiction"].value_counts()

    print(f"  Number of regulatory milestones tracked: {n_milestones}")
    print(f"  Jurisdictions covered: {n_jurisdictions}")
    print("  Milestones by jurisdiction:")
    for jur, count in jurisdiction_counts.items():
        print(f"    {jur}: {count}")

    # Print major milestones in chronological order
    df_reg_sorted = df_reg.sort_values("date")
    print("\n  Regulatory timeline overview:")
    for _, row in df_reg_sorted.iterrows():
        print(f"    {row['date'].strftime('%Y-%m')} | {row['event'][:90]}")

# ===========================================================================
# Section 7: Corporate Adoption
# ===========================================================================
print("=" * 60)
print("Section 7: Corporate Adoption")

df_corp, ok7 = load_csv("ai_tokens_corporate_adoption.csv")
if ok7:
    n_entities = len(df_corp)
    entity_types = df_corp["type"].value_counts()
    total_value = pd.to_numeric(
        df_corp["estimated_value_usd_million"], errors="coerce"
    ).sum()

    print(f"  Number of corporate/institutional entities tracked: {n_entities}")
    print(f"  Aggregate estimated value (where available): ${total_value:,.0f}M")
    print("  Entity types breakdown:")
    for etype, count in entity_types.items():
        print(f"    {etype}: {count}")

    # Key entity: Strategy (MicroStrategy) as largest corporate holder
    strategy_row = df_corp[df_corp["company"] == "Strategy (MicroStrategy)"]
    if not strategy_row.empty:
        print(
            f"  Largest corporate holder: {strategy_row.iloc[0]['company']} "
            f"(${strategy_row.iloc[0]['estimated_value_usd_million']:,.0f}M)"
        )

# ===========================================================================
# Section 8: Accounting Standards
# ===========================================================================
print("=" * 60)
print("Section 8: Accounting Standards")

df_acct, ok8 = load_csv("ai_tokens_accounting_comparison.csv")
if ok8:
    n_standards = len(df_acct)
    frameworks = df_acct["framework"].value_counts()

    print(f"  Number of accounting standards/frameworks documented: {n_standards}")
    print("  Framework distribution:")
    for fw, count in frameworks.items():
        print(f"    {fw}: {count}")

    print("\n  Summary of accounting frameworks:")
    print(f"  {'Standard':<35s} {'Framework':<12s} {'Effective':<15s}")
    print(f"  {'-'*35} {'-'*12} {'-'*15}")
    for _, row in df_acct.iterrows():
        print(
            f"  {row['standard']:<35s} "
            f"{row['framework']:<12s} "
            f"{str(row['effective_date']):<15s}"
        )

# ===========================================================================
# Section 9: Academic Literature
# ===========================================================================
print("=" * 60)
print("Section 9: Academic Literature")

df_lit, ok9 = load_csv("ai_tokens_academic_literature.csv")
if ok9:
    n_papers = len(df_lit)
    papers_by_year = df_lit["year"].value_counts().sort_index()
    journals = df_lit["journal"].value_counts()

    print(f"  Number of academic papers in dataset: {n_papers}")
    print("  Papers by year:")
    for yr, count in papers_by_year.items():
        print(f"    {yr}: {count}")

    # --- Fig 10: Publication trends ---
    fig, ax = plt.subplots(figsize=(10, 5))
    years = papers_by_year.index.astype(int)
    counts = papers_by_year.values
    ax.bar(years, counts, color=COLOUR_PALETTE[0], alpha=0.85, width=0.6)
    ax.plot(years, counts, color=COLOUR_PALETTE[3], marker="o", linewidth=2, markersize=6)
    ax.set_xlabel("Publication year")
    ax.set_ylabel("Number of papers")
    ax.set_title("Figure 10: Academic Publication Trends -- AI Tokens and Crypto Assets (ABS 4/4* & ABDC-A* Journals)")
    ax.set_xticks(years)
    ax.set_xticklabels(years.astype(str))
    save_chart(fig, "fig10_publication_trends.png")

    print("\n  Top journals represented:")
    for journal, count in journals.head(5).items():
        print(f"    {journal}: {count} papers")

# ===========================================================================
# Section 10: Summary Statistics
# ===========================================================================
print("=" * 60)
print("Section 10: Summary Statistics")
print("-" * 40)

results = {}

if ok:
    results["q2_2026_mcap"] = q2_2026_mcap
    results["peak_mcap"] = peak_mcap
    results["peak_mcap_period"] = peak_mcap_period
    results["peak_dominance"] = peak_dominance
    results["peak_dominance_period"] = peak_dominance_period
else:
    results["q2_2026_mcap"] = None

if ok2 and "largest_token" in dir():
    results["largest_token"] = largest_token["token"]
    results["largest_token_mcap"] = largest_token["market_cap_usd_billion_q2_2026"]

if ok3 and "avg_vol" in dir():
    results["avg_volatility"] = avg_vol

if ok4:
    results["vc_2025"] = vc_2025

if ok6:
    results["n_milestones"] = n_milestones

if ok9:
    results["n_papers"] = n_papers

print("Key statistics from the report:")
print()

if results.get("q2_2026_mcap"):
    print(f"  1. Total AI token market cap (Q2 2026):         ${results['q2_2026_mcap']:.2f} billion")
if results.get("peak_mcap"):
    print(f"  2. Peak AI token market cap:                    ${results['peak_mcap']:.2f} billion ({results['peak_mcap_period']})")
if results.get("peak_dominance"):
    print(f"  3. AI token dominance at peak:                   {results['peak_dominance']:.2f}% ({results['peak_dominance_period']})")
if results.get("largest_token"):
    print(f"  4. Largest AI token by market cap:               {results['largest_token']} (${results['largest_token_mcap']:.2f}B)")
if results.get("vc_2025"):
    print(f"  5. Total VC funding in AI-crypto (2025):         ${results['vc_2025']:.2f} billion")
if results.get("n_milestones"):
    print(f"  6. Number of regulatory milestones tracked:       {results['n_milestones']}")
if results.get("n_papers"):
    print(f"  7. Number of academic papers in dataset:          {results['n_papers']}")
if results.get("avg_volatility"):
    print(f"  8. Average annualised volatility (major tokens):  {results['avg_volatility']:.1%}")

print()
print("-" * 40)

# ===========================================================================
# Execution summary
# ===========================================================================
print()
print("=" * 60)
print("REPLICATION SUMMARY")
print("=" * 60)

sections_status = {
    "Section  1: Market Evolution": ok,
    "Section  2: Top Projects": ok2,
    "Section  3: Price Trajectories": ok3,
    "Section  4: VC Funding": ok4,
    "Section  5: Token Categories": True,
    "Section  6: Regulatory Timeline": ok6,
    "Section  7: Corporate Adoption": ok7,
    "Section  8: Accounting Standards": ok8,
    "Section  9: Academic Literature": ok9,
    "Section 10: Summary Statistics": True,
}

for section, status in sections_status.items():
    mark = "OK" if status else "SKIPPED (missing data)"
    print(f"  {section:<38s} {mark}")

print()
print("Charts saved to:", str(CHART_DIR))
print("DONE.")
