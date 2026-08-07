#!/usr/bin/env python3
"""
Replication Script: Understanding Large Language Models and Their
Implications for Accounting and Finance Research

Author: Dr Yuqian Zhang
Date:   2026-07-29
Purpose: Reproduces all charts and summary statistics from the main report.
         This script loads compiled CSV datasets from ../data/, generates
         eight publication-quality figures, and saves them to ../charts/.

Dependencies (install with pinned versions):
    pip install matplotlib==3.9.0 seaborn==0.13.2 pandas==2.2.2 numpy==1.26.4

Data notes:
    - All datasets under ../data/ were compiled from public sources as
      documented in data/README_methodology.txt.  The compilation process
      involved manual review and cross-referencing of multiple sources;
      therefore these datasets cannot be auto-downloaded from a single URL.
"""

import os
import sys
import warnings

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# ---------------------------------------------------------------------------
# 0.  Setup
# ---------------------------------------------------------------------------

SEED = 42
np.random.seed(SEED)

warnings.filterwarnings("ignore", category=FutureWarning)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "data")
CHARTS_DIR = os.path.join(SCRIPT_DIR, "..", "charts")

os.makedirs(CHARTS_DIR, exist_ok=True)

# Blue-green academic palette
PALETTE = ["#1e3a5f", "#059669", "#7c3aed", "#d97706", "#2d5a8e",
           "#10b981", "#9b5de5", "#dc2626", "#3d7abd", "#34d399"]
BLUE = "#1e3a5f"
GREEN = "#059669"
PURPLE = "#7c3aed"
ORANGE = "#d97706"

sns.set_style("whitegrid")
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.1,
})


# ---------------------------------------------------------------------------
# 1.  Data loading
# ---------------------------------------------------------------------------

def load_csv(filename):
    """Load a CSV from ../data/ with basic error handling."""
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Data file not found: {path}")
    return pd.read_csv(path, comment="#")


def check_columns(df, required, label):
    """Verify all required columns are present in the DataFrame."""
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"Missing columns in {label}: {missing}")


print("=" * 60)
print("Loading datasets ...")
print("=" * 60)

df_params = load_csv("llm_parameter_timeline.csv")
check_columns(df_params, ["model", "release_year", "parameters_billions",
                          "training_compute_flops", "developer"], "llm_parameter_timeline")
print(f"  llm_parameter_timeline.csv : {len(df_params)} rows")

df_arena = load_csv("llm_arena_scores.csv")
check_columns(df_arena, ["model", "year_quarter", "elo_score"], "llm_arena_scores")
print(f"  llm_arena_scores.csv       : {len(df_arena)} rows")

df_hallu = load_csv("llm_hallucination_rates.csv")
check_columns(df_hallu, ["model", "date_label", "hallucination_rate_pct"], "llm_hallucination_rates")
print(f"  llm_hallucination_rates.csv: {len(df_hallu)} rows")

df_adopt = load_csv("accounting_ai_adoption.csv")
check_columns(df_adopt, ["source", "year", "category", "percentage"], "accounting_ai_adoption")
print(f"  accounting_ai_adoption.csv : {len(df_adopt)} rows")

df_pubpol = load_csv("publisher_ai_policies.csv")
check_columns(df_pubpol, ["publisher", "policy_date_decimal", "policy_date_label"], "publisher_ai_policies")
print(f"  publisher_ai_policies.csv  : {len(df_pubpol)} rows")

df_reg = load_csv("ai_regulation_timeline.csv")
check_columns(df_reg, ["date", "event", "jurisdiction"], "ai_regulation_timeline")
print(f"  ai_regulation_timeline.csv : {len(df_reg)} rows")

df_pubs = load_csv("ai_accounting_publications.csv")
check_columns(df_pubs, ["year", "methodological_empirical", "conceptual_review", "total"], "ai_accounting_publications")
print(f"  ai_accounting_publications.csv: {len(df_pubs)} rows")

df_big4 = load_csv("big4_ai_investments.csv")
check_columns(df_big4, ["firm", "ai_platform", "investment_usd_billions"], "big4_ai_investments")
print(f"  big4_ai_investments.csv     : {len(df_big4)} rows")


# ---------------------------------------------------------------------------
# 2.  Summary statistics
# ---------------------------------------------------------------------------

def fmt_flops(val):
    """Human-readable FLOP string."""
    if val >= 1e27:
        return f"{val / 1e27:.1f} x 10^27"
    if val >= 1e24:
        return f"{val / 1e24:.1f} x 10^24"
    if val >= 1e21:
        return f"{val / 1e21:.1f} x 10^21"
    if val >= 1e18:
        return f"{val / 1e18:.1f} x 10^18"
    return f"{val:.2e}"


print("\n" + "=" * 60)
print("Summary Statistics")
print("=" * 60)

# --- Model parameters ---
print("\n-- LLM Parameter Timeline --")
print(f"Models in dataset: {len(df_params)}")
print(f"Year range: {df_params['release_year'].min()} - {df_params['release_year'].max()}")
print(f"Total parameters (largest model): {df_params['parameters_billions'].max():.0f}B "
      f"({df_params.loc[df_params['parameters_billions'].idxmax(), 'model']})")
max_flops = df_params["training_compute_flops"].max()
print(f"Training compute (largest): {fmt_flops(max_flops)} FLOP "
      f"({df_params.loc[df_params['training_compute_flops'].idxmax(), 'model']})")
print(f"Median parameters: {df_params['parameters_billions'].median():.1f}B")
print(f"Unique developers: {df_params['developer'].nunique()}")

# --- Arena scores ---
print("\n-- Arena Elo Scores --")
for model in df_arena["model"].unique():
    model_data = df_arena[df_arena["model"] == model]
    print(f"  {model}: min={model_data['elo_score'].min()}, "
          f"max={model_data['elo_score'].max()}, "
          f"delta={model_data['elo_score'].max() - model_data['elo_score'].min()}")

# --- Hallucination ---
print("\n-- Hallucination Rates --")
print(f"Rate range: {df_hallu['hallucination_rate_pct'].min():.1f}% - "
      f"{df_hallu['hallucination_rate_pct'].max():.1f}%")
print(f"Mean rate: {df_hallu['hallucination_rate_pct'].mean():.1f}%")
print(f"Best model: {df_hallu.loc[df_hallu['hallucination_rate_pct'].idxmin(), 'model']} "
      f"({df_hallu['hallucination_rate_pct'].min():.1f}%)")

# --- AI adoption ---
print("\n-- AI Adoption in Accounting --")
adopt_wk = df_adopt[df_adopt["source"] == "Wolters Kluwer"].copy()
if len(adopt_wk) > 0:
    print("  Wolters Kluwer survey: (category, 2024%, 2025%, change)")
    for cat in adopt_wk["category"].unique():
        sub = adopt_wk[adopt_wk["category"] == cat]
        v24 = sub[sub["year"] == 2024]["percentage"].values
        v25 = sub[sub["year"] == 2025]["percentage"].values
        if len(v24) > 0 and len(v25) > 0:
            change = int(v25[0]) - int(v24[0])
            arrow = "+" if change > 0 else ""
            print(f"    {cat:<22} {int(v24[0]):>4}%   {int(v25[0]):>4}%   {arrow}{change}pp")
adopt_tr = df_adopt[df_adopt["source"] == "Thomson Reuters"]
if len(adopt_tr) > 0:
    print("  Thomson Reuters 2025 survey (tax firms):")
    for _, row in adopt_tr.iterrows():
        print(f"    {row['category']}: {int(row['percentage'])}%")

# --- Publications ---
print("\n-- AI Publications in Top Accounting Journals --")
print(f"Year range: {df_pubs['year'].min()} - {df_pubs['year'].max()}")
print(f"Total publications (all years): {df_pubs['total'].sum()}")
first_year = df_pubs[df_pubs["year"] == df_pubs["year"].min()]
last_year = df_pubs[df_pubs["year"] == df_pubs["year"].max()]
print(f"Growth: {last_year['total'].values[0]} publications in "
      f"{int(last_year['year'].values[0])} vs {first_year['total'].values[0]} in "
      f"{int(first_year['year'].values[0])}")
emp_total = df_pubs["methodological_empirical"].sum()
con_total = df_pubs["conceptual_review"].sum()
print(f"Methodological/Empirical: {emp_total} ({emp_total / df_pubs['total'].sum() * 100:.0f}%)")
print(f"Conceptual/Review:        {con_total} ({con_total / df_pubs['total'].sum() * 100:.0f}%)")

# --- Big Four ---
print("\n-- Big Four AI Investments --")
print(f"Total investment: USD {df_big4['investment_usd_billions'].sum():.1f} billion")
for _, row in df_big4.iterrows():
    print(f"  {row['firm']}: USD {row['investment_usd_billions']:.1f}B - {row['ai_platform']}")


# ---------------------------------------------------------------------------
# 3.  Chart 1: Training Compute (bar, log scale, 2017-2026)
# ---------------------------------------------------------------------------

print("\n" + "=" * 60)
print("Generating charts ...")
print("=" * 60)

yearly = df_params.groupby("release_year").agg(
    max_flops=("training_compute_flops", "max"),
    model=("model", lambda x: list(x))
).reset_index()
yearly = yearly.sort_values("release_year")

fig, ax = plt.subplots(figsize=(10, 5.5))
bars = ax.bar(yearly["release_year"].astype(str), yearly["max_flops"],
              color=BLUE, edgecolor="white", linewidth=0.5, width=0.65)

ax.set_yscale("log")
ax.set_ylabel("Training Compute (FLOP)")
ax.set_xlabel("Year")
ax.set_title("Figure 1: Training Compute for Notable AI Models (2017-2026)", fontweight="bold")

for bar, (_, row) in zip(bars, yearly.iterrows()):
    model_str = "/".join(row["model"])
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.15,
            model_str, ha="center", va="bottom", fontsize=10,
            fontweight="bold", color="#1c1917")

ax.yaxis.set_major_formatter(mticker.FuncFormatter(
    lambda x, _: "10$^{%d}$" % int(np.log10(x)) if x >= 1 else f"{x:.0f}"))
ax.tick_params(axis="x", rotation=0)
sns.despine()

path = os.path.join(CHARTS_DIR, "chart1_training_compute.png")
fig.savefig(path)
plt.close(fig)
print(f"  [1/8] {path}")


# ---------------------------------------------------------------------------
# 4.  Chart 2: Parameter Counts (bar, log scale)
# ---------------------------------------------------------------------------

df_p2 = df_params.sort_values("release_year", ascending=True).copy()

fig, ax = plt.subplots(figsize=(12, 5.5))
colors_2 = [PALETTE[i % len(PALETTE)] for i in range(len(df_p2))]
bars = ax.bar(df_p2["model"], df_p2["parameters_billions"],
              color=colors_2, edgecolor="white", linewidth=0.3, width=0.7)

ax.set_yscale("log")
ax.set_ylabel("Parameters (billions)")
ax.set_title("Figure 2: Parameter Count of Major LLMs by Release Date (2017-2026)",
             fontweight="bold")
ax.tick_params(axis="x", rotation=45, labelsize=9)
sns.despine()

path = os.path.join(CHARTS_DIR, "chart2_parameter_counts.png")
fig.savefig(path)
plt.close(fig)
print(f"  [2/8] {path}")


# ---------------------------------------------------------------------------
# 5.  Chart 3: Arena Elo Scores (multi-line, 2023-2026)
# ---------------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(10, 5.5))

markers = ["o", "s", "D", "^", "v", "p", "*", "X"]
for i, model in enumerate(sorted(df_arena["model"].unique())):
    sub = df_arena[df_arena["model"] == model].sort_values("year_quarter")
    ax.plot(sub["year_quarter"], sub["elo_score"],
            marker=markers[i % len(markers)], markersize=6,
            label=model, linewidth=1.8, color=PALETTE[i % len(PALETTE)])

ax.set_xlabel("Year")
ax.set_ylabel("Elo Score")
ax.set_title("Figure 3: LMSYS Chatbot Arena Elo Scores (2023-2026)", fontweight="bold")
ax.set_xlim(2023, 2026.75)
ax.legend(loc="lower right", fontsize=8, frameon=True)
sns.despine()

path = os.path.join(CHARTS_DIR, "chart3_arena_elo.png")
fig.savefig(path)
plt.close(fig)
print(f"  [3/8] {path}")


# ---------------------------------------------------------------------------
# 6.  Chart 4: Hallucination Rates (horizontal bar)
# ---------------------------------------------------------------------------

df_h = df_hallu.sort_values("hallucination_rate_pct", ascending=True).copy()

def hallu_color(val):
    if val < 2:
        return GREEN
    if val < 5:
        return "#10b981"
    if val < 8:
        return ORANGE
    return "#dc2626"

fig, ax = plt.subplots(figsize=(9, 5))
colors_h = [hallu_color(v) for v in df_h["hallucination_rate_pct"]]
bars = ax.barh(df_h["model"], df_h["hallucination_rate_pct"],
               color=colors_h, edgecolor="white", height=0.6)

for bar, val in zip(bars, df_h["hallucination_rate_pct"]):
    ax.text(bar.get_width() + 0.15, bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}%", va="center", fontsize=10)

ax.set_xlabel("Hallucination Rate (%)")
ax.set_title("Figure 4: Hallucination Rates on Document Summarisation (2024-2026)",
             fontweight="bold")
ax.set_xlim(0, df_h["hallucination_rate_pct"].max() * 1.25)
sns.despine()

path = os.path.join(CHARTS_DIR, "chart4_hallucination_rates.png")
fig.savefig(path)
plt.close(fig)
print(f"  [4/8] {path}")


# ---------------------------------------------------------------------------
# 7.  Chart 5: AI Adoption in Accounting (grouped bar)
# ---------------------------------------------------------------------------

df_a = df_adopt[df_adopt["source"] == "Wolters Kluwer"].copy()
categories_ordered = ["Using GenAI", "Planning or considering", "No current plans"]
df_a = df_a[df_a["category"].isin(categories_ordered)]
pivot = df_a.pivot(index="category", columns="year", values="percentage")
pivot = pivot.reindex(categories_ordered)
categories = pivot.index.tolist()

fig, ax = plt.subplots(figsize=(9, 5))
x = np.arange(len(categories))
width = 0.35

vals_2024 = [pivot.at[c, 2024] if 2024 in pivot.columns else 0 for c in categories]
vals_2025 = [pivot.at[c, 2025] if 2025 in pivot.columns else 0 for c in categories]

bars1 = ax.barh(x - width / 2, vals_2024, width,
                label="2024", color="#9fc3b5", edgecolor="white")
bars2 = ax.barh(x + width / 2, vals_2025, width,
                label="2025", color="#1f4d3f", edgecolor="white")

ax.set_yticks(x)
ax.set_yticklabels(categories)
ax.set_xlabel("Percentage of Firms")
ax.set_title("Figure 5: AI Adoption in Accounting Firms (2024 vs 2025)", fontweight="bold")
ax.set_xlim(0, 100)
ax.invert_yaxis()

for bars_obj in [bars1, bars2]:
    for bar in bars_obj:
        w = bar.get_width()
        ax.text(w + 1, bar.get_y() + bar.get_height() / 2,
                f"{w:.0f}%", va="center", fontsize=10)

ax.legend(loc="lower right")
sns.despine()

path = os.path.join(CHARTS_DIR, "chart5_ai_adoption.png")
fig.savefig(path)
plt.close(fig)
print(f"  [5/8] {path}")


# ---------------------------------------------------------------------------
# 8.  Chart 6: Publisher AI Policies (scatter timeline)
# ---------------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(9, 4.5))

y_positions = list(range(len(df_pubpol)))
ax.scatter(df_pubpol["policy_date_decimal"], y_positions,
           s=120, color=BLUE, zorder=5)

for i, (_, row) in enumerate(df_pubpol.iterrows()):
    ax.text(row["policy_date_decimal"] + 0.05, i,
            f"{row['publisher']} ({row['policy_date_label']})",
            va="center", fontsize=10)

ax.set_yticks([])
ax.set_xlim(2022.5, 2025.5)
ax.set_ylim(-0.8, len(df_pubpol) - 0.2)
ax.set_xlabel("Year")
ax.set_title("Figure 6: Publisher AI Policy Adoption Timeline (2023-2024)",
             fontweight="bold")
sns.despine(left=True)

path = os.path.join(CHARTS_DIR, "chart6_publisher_policies.png")
fig.savefig(path)
plt.close(fig)
print(f"  [6/8] {path}")


# ---------------------------------------------------------------------------
# 9.  Chart 7: AI Regulation Timeline (scatter)
# ---------------------------------------------------------------------------

jurisdiction_colors = {
    "EU": BLUE,
    "US": GREEN,
    "China": ORANGE,
    "International": PURPLE,
}

df_reg["date_dt"] = pd.to_datetime(df_reg["date"])
df_reg = df_reg.sort_values("date_dt")

fig, ax = plt.subplots(figsize=(11, 6))

for i, (_, row) in enumerate(df_reg.iterrows()):
    color = jurisdiction_colors.get(row["jurisdiction"], BLUE)
    ax.scatter(row["date_dt"], i, s=100, color=color, zorder=5, edgecolors="white", linewidth=0.5)
    ax.text(row["date_dt"], i + 0.3,
            f"{row['event']}\n({row['jurisdiction']})",
            ha="left" if i % 2 == 0 else "left",
            va="bottom", fontsize=8.5,
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8, edgecolor="none"))

ax.set_yticks([])
ax.set_xlabel("Date")
ax.set_title("Figure 7: Major Global AI Regulatory Milestones (2021-2026)", fontweight="bold")
ax.set_xlim(pd.Timestamp("2021-01-01"), pd.Timestamp("2027-06-30"))
ax.set_ylim(-1, len(df_reg) + 0.5)

legend_elements = [plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=c,
                               markersize=10, label=j)
                   for j, c in jurisdiction_colors.items()]
ax.legend(handles=legend_elements, loc="lower right", fontsize=9, frameon=True)
sns.despine(left=True)

path = os.path.join(CHARTS_DIR, "chart7_regulation_timeline.png")
fig.savefig(path)
plt.close(fig)
print(f"  [7/8] {path}")


# ---------------------------------------------------------------------------
# 10. Chart 8: AI Publications (stacked bar, 2017-2026)
# ---------------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(10, 5))
years = df_pubs["year"].astype(str).tolist()

ax.bar(years, df_pubs["methodological_empirical"], label="Methodological/Empirical",
       color=BLUE, edgecolor="white", linewidth=0.3)
ax.bar(years, df_pubs["conceptual_review"],
       bottom=df_pubs["methodological_empirical"], label="Conceptual/Review",
       color=PURPLE, edgecolor="white", linewidth=0.3)

for i, (_, row) in enumerate(df_pubs.iterrows()):
    total_h = row["methodological_empirical"] + row["conceptual_review"]
    ax.text(i, total_h + 1.5, str(int(total_h)), ha="center", fontsize=9, fontweight="bold")

ax.set_xlabel("Year")
ax.set_ylabel("Number of Publications")
ax.set_title("Figure 8: AI-Related Publications in Top Accounting Journals (2017-2026)",
             fontweight="bold")
ax.legend(loc="upper left", fontsize=9)
sns.despine()

path = os.path.join(CHARTS_DIR, "chart8_ai_publications.png")
fig.savefig(path)
plt.close(fig)
print(f"  [8/8] {path}")


# ---------------------------------------------------------------------------
# 11. Done
# ---------------------------------------------------------------------------

print("\n" + "=" * 60)
print("Replication complete.")
print(f"Charts saved to: {os.path.abspath(CHARTS_DIR)}/")
print("=" * 60)
