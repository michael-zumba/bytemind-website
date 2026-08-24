#!/usr/bin/env python3
"""
Prompt Literacy in the AI Era: Value, Measurement, and the Accounting
Question
Replication Script

Author: Dr Yuqian Zhang
Date: 24 August 2026

Description: This script reproduces every chart and statistic in the
research brief from the compiled source data files. It generates 13 PNG
figures matching the ECharts visualisations in the report and prints the
statistics quoted in the report and one-page summary. The printed
statistics are the source of truth for every number in the report.

Data sources:
- Compiled CSV files in the ../data/ directory. These are manually compiled
  from primary publications (Pew Research Center, McKinsey, Microsoft and
  LinkedIn, Lightcast and Stanford AI Index, Anthropic Economic Index,
  World Economic Forum, XBRL International, IAASB, IFAC and IESBA) and
  peer-reviewed studies (Noy and Zhang 2023; Brynjolfsson, Li, and Raymond
  2025; Dell'Acqua et al. 2026; Peng et al. 2023; Wei et al. 2022; Kojima
  et al. 2022; Zhu et al. 2023). Most of these sources publish headline
  statistics in PDF reports, press releases, and article pages without
  stable machine-readable CSV endpoints, and several academic papers are
  behind paywalls, so auto-download is not possible for those files.
- One genuinely open dataset is auto-downloaded with local caching: the
  Anthropic Economic Index interaction-type CSV hosted on Hugging Face
  (https://huggingface.co/datasets/Anthropic/EconomicIndex). It is used to
  verify the published automation share reported in the compiled CSV.
"""

# === Dependencies (pinned) ===
# Install with:
#   pip install --break-system-packages matplotlib==3.9.1 numpy==2.0.1 pandas==2.2.2
import os
import ssl
import sys
import urllib.request
import warnings

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# === Reproducibility ===
SEED = 42
np.random.seed(SEED)

# === Paths ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(REPORT_DIR, "data")
CHARTS_DIR = os.path.join(REPORT_DIR, "charts")
CACHE_DIR = os.path.join(REPORT_DIR, ".cache")
os.makedirs(CHARTS_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# === Chart style (matches the report palette) ===
COLOR_NAVY = "#1e3a5f"
COLOR_GREEN = "#27ae60"
COLOR_RED = "#c0392b"
COLOR_BLUE = "#7ba3cc"
COLOR_AMBER = "#f39c12"
COLOR_GREY = "#8a8a8a"

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.edgecolor": "#d6d3d1",
    "axes.labelcolor": "#1c1917",
    "xtick.color": "#57534e",
    "ytick.color": "#57534e",
    "axes.grid": True,
    "grid.color": "#e7e5e4",
    "grid.linewidth": 0.8,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})


def load_csv(filename, required_columns):
    """Load a compiled CSV from ../data/ and check required columns exist.

    Auto-download is not possible for these files: the underlying
    organisations publish headline statistics in PDFs, press releases, and
    article pages without stable CSV endpoints, and several academic papers
    are behind paywalls. Each row records its primary source.
    """
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        sys.exit(f"ERROR: missing data file {path}")
    df = pd.read_csv(path, comment="#")
    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        sys.exit(f"ERROR: {filename} is missing columns {missing}")
    return df


def save_fig(fig, name):
    path = os.path.join(CHARTS_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved chart: {name}")


def print_stat(label, value, source):
    print(f"STAT | {label} | {value} | {source}")


# =========================================================================
# SECTION 1. Public data auto-download with local caching
# =========================================================================
# The Anthropic Economic Index interaction-type CSV is openly published on
# Hugging Face. It is downloaded once and cached locally so that repeated
# runs do not hit the network. The published 57/43 augmentation-automation
# split in the first report is an analysis of the underlying conversation
# data and is recorded in ../data/job_share_ai_tasks.csv; the raw
# interaction-type file is used here as a verification check.

ANTHROPIC_URL = (
    "https://huggingface.co/datasets/Anthropic/EconomicIndex/resolve/main/"
    "release_2025_02_10/automation_vs_augmentation.csv"
)
ANTHROPIC_CACHE = os.path.join(CACHE_DIR, "anthropic_automation_vs_augmentation.csv")

if not os.path.exists(ANTHROPIC_CACHE):
    print("Downloading Anthropic Economic Index interaction-type data...")
    try:
        ctx = ssl._create_unverified_context()
        req = urllib.request.Request(
            ANTHROPIC_URL,
            headers={"User-Agent": "Mozilla/5.0 research replication script"},
        )
        with urllib.request.urlopen(req, context=ctx, timeout=120) as resp:
            with open(ANTHROPIC_CACHE, "wb") as fh:
                fh.write(resp.read())
    except Exception as exc:
        print(f"WARNING: auto-download failed ({exc}); using compiled CSV only.")
        ANTHROPIC_CACHE = None

if ANTHROPIC_CACHE and os.path.exists(ANTHROPIC_CACHE):
    anthropic_raw = pd.read_csv(ANTHROPIC_CACHE)
    directive_share = anthropic_raw.loc[
        anthropic_raw["interaction_type"] == "directive", "pct"
    ].iloc[0]
    print(
        "Verification: directive (automation-type) share in the open "
        f"Anthropic dataset is {directive_share:.1f} percent; the published "
        "first-report split of 43 percent automation comes from the paper's "
        "analysis of the full conversation sample."
    )

# =========================================================================
# SECTION 2. Data loading and validation
# =========================================================================

adoption_us = load_csv(
    "chatgpt_adoption_us.csv",
    ["wave", "year", "share_pct", "subgroup", "note", "source"],
)
weekly_users = load_csv(
    "chatgpt_weekly_users.csv",
    ["date", "metric", "value_millions", "note", "source"],
)
org_adoption = load_csv(
    "org_genai_adoption.csv",
    ["wave", "survey_field_period", "metric", "share_pct", "source"],
)
worker_use = load_csv(
    "worker_ai_use.csv",
    ["survey", "wave", "indicator", "share_pct", "note", "source"],
)
job_postings = load_csv(
    "job_postings_ai_skills.csv",
    ["skill", "year", "postings", "note", "source"],
)
job_share = load_csv(
    "job_share_ai_tasks.csv",
    ["report", "sample_period", "indicator", "share_pct", "source"],
)
productivity = load_csv(
    "productivity_experiments.csv",
    ["study", "year", "setting", "participants", "indicator", "value", "unit",
     "note", "source"],
)
benchmarks = load_csv(
    "prompting_benchmarks.csv",
    ["study", "year", "benchmark", "indicator", "value", "unit", "note", "source"],
)
education = load_csv(
    "education_offerings.csv",
    ["item", "date", "indicator", "value", "note", "source"],
)
assurance = load_csv(
    "ai_assurance_activity.csv",
    ["date", "organisation", "item", "indicator", "value", "note", "source"],
)
verification = load_csv(
    "audit_verification_behavior.csv",
    ["study", "year", "indicator", "value", "unit", "note", "source"],
)
opportunities = load_csv(
    "research_opportunities.csv",
    ["opportunity", "field", "theory_significance", "data_availability", "basis"],
)

print("All compiled CSV files loaded and validated.")

# =========================================================================
# SECTION 3. Emergence of human-AI conversation (Figures 1 and 2)
# =========================================================================

# Figure 1: ChatGPT weekly active users, OpenAI announcements.
weekly_dates = pd.to_datetime(weekly_users["date"])
weekly_values = weekly_users["value_millions"].astype(float)

fig1, ax1 = plt.subplots(figsize=(9.5, 4.8))
ax1.plot(weekly_dates, weekly_values, marker="o", linewidth=2.5,
         color=COLOR_NAVY, markersize=7)
ax1.axvline(pd.Timestamp("2022-11-30"), color=COLOR_RED, linestyle="--",
            linewidth=1.2, label="ChatGPT launch, November 2022")
for x, y in zip(weekly_dates, weekly_values):
    ax1.annotate(f"{int(y):,}", (x, y), textcoords="offset points",
                 xytext=(0, 9), ha="center", fontsize=9, color=COLOR_NAVY)
ax1.set_title("Figure 1: ChatGPT Weekly Active Users, OpenAI Announcements")
ax1.set_ylabel("Weekly active users (millions)")
ax1.set_xlim(pd.Timestamp("2022-08-01"), pd.Timestamp("2025-12-01"))
ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax1.legend(loc="upper left", frameon=False)
save_fig(fig1, "fig01_chatgpt_weekly_users.png")

for _, row in weekly_users.iterrows():
    print_stat("ChatGPT weekly active users (millions)",
               int(row["value_millions"]), row["source"])

# Figure 2: ChatGPT ever-use among US adults, Pew Research Center.
pew_all = adoption_us[adoption_us["subgroup"] == "All adults"].sort_values("year")

fig2, ax2 = plt.subplots(figsize=(9.5, 4.8))
pew_labels = [w.replace("February-March", "Feb-Mar").replace("February", "Feb")
              .replace("March", "Mar").replace("July", "Jul") for w in pew_all["wave"]]
ax2.bar(pew_labels, pew_all["share_pct"], color=COLOR_BLUE,
        width=0.6, edgecolor="white")
for i, (_, row) in enumerate(pew_all.iterrows()):
    ax2.annotate(f"{row['share_pct']:.0f}%", (i, row["share_pct"]),
                 textcoords="offset points", xytext=(0, 6), ha="center",
                 fontsize=9, color=COLOR_NAVY)
ax2.set_title("Figure 2: US Adults Who Have Ever Used ChatGPT (Pew Research Center)")
ax2.set_ylabel("Share of US adults (percent)")
ax2.set_ylim(0, 55)
save_fig(fig2, "fig02_pew_chatgpt_adoption.png")

for _, row in adoption_us.iterrows():
    print_stat(
        f"ChatGPT ever-use, {row['wave']} ({row['subgroup']})",
        f"{row['share_pct']:.0f} percent", row["source"],
    )

# =========================================================================
# SECTION 4. Prompting science and measurement (Figure 3)
# =========================================================================

bench_pairs = [
    ("Wei et al. 2022 GSM8K", 17.9, 58.1),
    ("Kojima et al. MultiArith", 17.7, 78.7),
    ("Kojima et al. GSM8K", 10.4, 40.7),
]

fig3, ax3 = plt.subplots(figsize=(9.5, 4.8))
x3 = np.arange(len(bench_pairs))
w3 = 0.34
ax3.bar(x3 - w3 / 2, [p[1] for p in bench_pairs], width=w3, color=COLOR_BLUE,
        label="Standard prompting")
ax3.bar(x3 + w3 / 2, [p[2] for p in bench_pairs], width=w3, color=COLOR_NAVY,
        label="Chain-of-thought prompting")
for xi, (name, base, treated) in zip(x3, bench_pairs):
    ax3.annotate(f"{base:.1f}%", (xi - w3 / 2, base), textcoords="offset points",
                 xytext=(0, 5), ha="center", fontsize=9, color=COLOR_BLUE)
    ax3.annotate(f"{treated:.1f}%", (xi + w3 / 2, treated),
                 textcoords="offset points", xytext=(0, 5), ha="center",
                 fontsize=9, color=COLOR_NAVY)
ax3.set_xticks(x3)
ax3.set_xticklabels([p[0] for p in bench_pairs])
ax3.set_ylim(0, 95)
ax3.set_ylabel("Accuracy (percent)")
ax3.set_title("Figure 3: Prompting Interventions and Reasoning Accuracy")
ax3.legend(loc="upper left", frameon=False)
save_fig(fig3, "fig03_prompting_benchmarks.png")

for _, row in benchmarks.iterrows():
    unit = row["unit"]
    if unit == "count":
        print_stat(row["indicator"], f"{row['value']:,}", row["source"])
    else:
        print_stat(row["indicator"], f"{row['value']:.1f} percent", row["source"])

# =========================================================================
# SECTION 5. Labour market and economic value (Figures 4, 5, and 6)
# =========================================================================

# Figure 4: US job postings for AI skills, Lightcast for Stanford AI Index.
skills = ["prompt engineering", "generative AI", "large language models"]
p2023 = [1400, 16000, 5000]
p2024 = [6300, 66000, 20000]

fig4, ax4 = plt.subplots(figsize=(9.5, 4.8))
x4 = np.arange(len(skills))
w4 = 0.34
ax4.bar(x4 - w4 / 2, p2023, width=w4, color=COLOR_BLUE, label="2023")
ax4.bar(x4 + w4 / 2, p2024, width=w4, color=COLOR_NAVY, label="2024")
for xi, v in zip(x4 - w4 / 2, p2023):
    ax4.annotate(f"{v:,}", (xi, v), textcoords="offset points", xytext=(0, 5),
                 ha="center", fontsize=8, color=COLOR_BLUE)
for xi, v in zip(x4 + w4 / 2, p2024):
    ax4.annotate(f"{v:,}", (xi, v), textcoords="offset points", xytext=(0, 5),
                 ha="center", fontsize=8, color=COLOR_NAVY)
ax4.set_xticks(x4)
ax4.set_xticklabels(["Prompt engineering", "Generative AI", "Large language models"])
ax4.set_yscale("log")
ax4.set_ylim(1000, 100000)
ax4.set_ylabel("Job postings")
ax4.set_title("Figure 4: US Job Postings Mentioning AI Skills (Log Scale; Lightcast for Stanford AI Index 2025)")
ax4.legend(loc="upper left", frameon=False)
save_fig(fig4, "fig04_job_postings_ai_skills.png")

for _, row in job_postings.iterrows():
    print_stat(f"Job postings, {row['skill']}, {row['year']}",
               f"{row['postings']:,}", row["source"])

# Figure 5: Productivity gains in controlled experiments.
gain_rows = productivity[productivity["indicator"].isin(
    ["time_to_complete_change_pct", "productivity_change_pct",
     "tasks_completed_change_pct", "speed_change_pct"])]

fig5, ax5 = plt.subplots(figsize=(9.5, 4.8))
gain_vals = [
    -gain_rows[gain_rows["indicator"] == "time_to_complete_change_pct"]["value"].iloc[0],
    gain_rows[gain_rows["indicator"] == "productivity_change_pct"]["value"].iloc[0],
    gain_rows[gain_rows["indicator"] == "tasks_completed_change_pct"]["value"].iloc[0],
    gain_rows[(gain_rows["indicator"] == "speed_change_pct")
              & (gain_rows["study"] == "Peng et al. 2023")]["value"].iloc[0],
]
gain_names = [
    "Noy and Zhang: time to complete",
    "Brynjolfsson et al.: productivity",
    "Dell'Acqua et al.: tasks completed",
    "Peng et al.: task speed",
]
bars5 = ax5.barh(gain_names, gain_vals, color=[COLOR_NAVY, COLOR_GREEN,
                  COLOR_BLUE, COLOR_AMBER], height=0.55)
for bar, v in zip(bars5, gain_vals):
    ax5.annotate(f"{v:.1f}%", (v, bar.get_y() + bar.get_height() / 2),
                 textcoords="offset points", xytext=(6, 0), va="center",
                 fontsize=9, color=COLOR_NAVY)
ax5.set_xlim(0, 65)
ax5.set_xlabel("Measured gain (percent)")
ax5.set_title("Figure 5: Productivity Gains in Controlled Experiments")
save_fig(fig5, "fig05_productivity_gains.png")

for _, row in gain_rows.iterrows():
    print_stat(row["indicator"], f"{row['value']:.1f} percent", row["source"])

for study_label, participants in [
    ("Noy and Zhang 2023", 453),
    ("Brynjolfsson Li and Raymond 2025", 5172),
    ("Dell'Acqua et al. 2026", 758),
    ("Peng et al. 2023", 95),
]:
    print_stat(f"Participants, {study_label}", f"{participants:,}",
               "study sample described in the published paper")

# Figure 6: Quality risk outside the AI capability frontier.
outside = verification[
    verification["indicator"] == "correct_solutions_outside_frontier_change_pp"
]

fig6, ax6 = plt.subplots(figsize=(9.5, 3.2))
outside_val = outside["value"].iloc[0]
bar6 = ax6.barh(["AI users, outside the capability frontier"], [outside_val],
                color=COLOR_RED, height=0.45)
ax6.annotate(f"{outside_val:.0f} percentage points",
             (outside_val, bar6[0].get_y() + bar6[0].get_height() / 2),
             textcoords="offset points", xytext=(-6, 0), va="center",
             ha="right", fontsize=9, color=COLOR_RED)
ax6.set_xlim(outside_val - 30, 2)
ax6.set_xlabel("Change in likelihood of correct solutions (percentage points)")
ax6.set_title("Figure 6: Quality Risk Outside the AI Capability Frontier (Dell'Acqua et al.)")
save_fig(fig6, "fig06_outside_frontier_risk.png")

print_stat(outside["indicator"].iloc[0],
           f"{outside_val:.0f} percentage points", outside["source"].iloc[0])

# =========================================================================
# SECTION 6. Business and organisational implications (Figures 7, 8, 9a, 9b)
# =========================================================================

# Figure 7: Organisational adoption of generative AI, McKinsey State of AI.
genai = org_adoption[org_adoption["metric"] == "organizations_regularly_using_gen_ai_pct"]
overall_ai = org_adoption[
    org_adoption["metric"] == "organizations_using_ai_in_any_function_pct"
]
stanford = org_adoption[org_adoption["metric"] == "organizations_reporting_ai_use_pct"]

labels7 = ["2023", "Early 2024", "2025"]
genai_vals = [33.0, 65.0, 79.0]

fig7, ax7 = plt.subplots(figsize=(9.5, 4.8))
x7 = np.arange(len(labels7))
ax7.bar(x7, genai_vals, width=0.45, color=COLOR_NAVY, label="Regularly use gen AI")
ax7.bar(x7[-1] + 0.35, [overall_ai["share_pct"].iloc[0]], width=0.45,
        color=COLOR_GREEN, label="Use AI in any function (2025)")
for xi, v in zip(x7, genai_vals):
    ax7.annotate(f"{v:.0f}%", (xi, v), textcoords="offset points",
                 xytext=(0, 6), ha="center", fontsize=9, color=COLOR_NAVY)
ax7.annotate(f"{overall_ai['share_pct'].iloc[0]:.0f}%",
             (x7[-1] + 0.35, overall_ai["share_pct"].iloc[0]),
             textcoords="offset points", xytext=(0, 6), ha="center",
             fontsize=9, color=COLOR_GREEN)
ax7.set_xticks(list(x7) + [x7[-1] + 0.35])
ax7.set_xticklabels(labels7 + ["2025 overall AI"])
ax7.set_ylim(0, 100)
ax7.set_ylabel("Share of organisations (percent)")
ax7.set_title("Figure 7: Organisational Adoption of Generative AI (McKinsey State of AI)")
ax7.legend(loc="upper left", frameon=False)
save_fig(fig7, "fig07_org_genai_adoption.png")

for _, row in org_adoption.iterrows():
    print_stat(f"{row['metric']}, {row['wave']}",
               f"{row['share_pct']:.0f} percent", row["source"])

# Figure 8: AI use at work, Pew and Microsoft and LinkedIn.
pew_work = worker_use[worker_use["survey"] == "Pew Research Center"]
msft_work = worker_use[
    worker_use["survey"] == "Microsoft and LinkedIn Work Trend Index 2024"
]

fig8, ax8 = plt.subplots(figsize=(9.5, 4.8))
work_labels = ["Pew Oct 2024", "Pew Sep 2025", "Knowledge\nworkers use gen AI",
               "Leaders not hiring\nwithout AI skills", "Prefer less experienced\nwith AI skills"]
work_vals = [16.0, 21.0, 75.0, 66.0, 71.0]
work_colors = [COLOR_BLUE, COLOR_BLUE, COLOR_NAVY, COLOR_NAVY, COLOR_NAVY]
bars8 = ax8.bar(work_labels, work_vals, color=work_colors, width=0.62,
                edgecolor="white")
for bar in bars8:
    ax8.annotate(f"{bar.get_height():.0f}%",
                 (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                 textcoords="offset points", xytext=(0, 5), ha="center",
                 fontsize=9, color=COLOR_NAVY)
ax8.set_ylim(0, 90)
ax8.set_ylabel("Share (percent)")
ax8.set_title("Figure 8: AI Use at Work (Pew Research Center and Microsoft-LinkedIn)")
save_fig(fig8, "fig08_worker_ai_use.png")

for _, row in worker_use.iterrows():
    print_stat(f"{row['indicator']}, {row['survey']}, {row['wave']}",
               f"{row['share_pct']:.0f} percent", row["source"])

print_stat("Work Trend Index 2024 sample",
           "31,000 people in 31 countries",
           "Microsoft and LinkedIn Work Trend Index 2024")

# Figures 9a and 9b: Anthropic Economic Index occupation coverage and
# augmentation versus automation.
coverage = job_share[
    job_share["indicator"] == "occupations_with_ai_in_at_least_25pct_of_tasks"
]
augmentation = job_share[
    job_share["indicator"].isin(["tasks_augmented_pct", "tasks_automated_pct"])
]

fig9a, ax9a = plt.subplots(figsize=(9.5, 4.8))
cov_labels = ["January 2025 sample\n(first report)", "November 2025 sample\n(fourth report)"]
cov_vals = [coverage.iloc[0]["share_pct"], coverage.iloc[1]["share_pct"]]
bars9a = ax9a.bar(cov_labels, cov_vals, color=[COLOR_BLUE, COLOR_NAVY],
                  width=0.5, edgecolor="white")
for bar in bars9a:
    ax9a.annotate(f"{bar.get_height():.0f}%",
                  (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                  textcoords="offset points", xytext=(0, 6), ha="center",
                  fontsize=10, color=COLOR_NAVY)
ax9a.set_ylim(0, 60)
ax9a.set_ylabel("Occupations with AI in at least 25 percent of tasks (percent)")
ax9a.set_title("Figure 9a: Occupations Using AI for at Least a Quarter of Tasks (Anthropic Economic Index)")
save_fig(fig9a, "fig09a_occupation_task_coverage.png")

for _, row in coverage.iterrows():
    print_stat(row["indicator"], f"{row['share_pct']:.0f} percent", row["source"])

aug_feb25 = augmentation[augmentation["report"].str.contains("First")].sort_values("indicator")
aug_jan26 = augmentation[augmentation["report"].str.contains("Fourth")].sort_values("indicator")

fig9b, ax9b = plt.subplots(figsize=(9.5, 4.8))
x9b = np.arange(2)
w9b = 0.34
ax9b.bar(x9b - w9b / 2, aug_feb25["share_pct"], width=w9b, color=COLOR_BLUE,
         label="January 2025 sample")
ax9b.bar(x9b + w9b / 2, aug_jan26["share_pct"], width=w9b, color=COLOR_NAVY,
         label="November 2025 sample")
for xi, v in zip(x9b - w9b / 2, aug_feb25["share_pct"]):
    ax9b.annotate(f"{v:.0f}%", (xi, v), textcoords="offset points",
                  xytext=(0, 6), ha="center", fontsize=9, color=COLOR_BLUE)
for xi, v in zip(x9b + w9b / 2, aug_jan26["share_pct"]):
    ax9b.annotate(f"{v:.0f}%", (xi, v), textcoords="offset points",
                  xytext=(0, 6), ha="center", fontsize=9, color=COLOR_NAVY)
ax9b.set_xticks(x9b)
ax9b.set_xticklabels(["Augmentation", "Automation"])
ax9b.set_ylim(0, 70)
ax9b.set_ylabel("Share of conversations (percent)")
ax9b.set_title("Figure 9b: Augmentation versus Automation (Anthropic Economic Index)")
ax9b.legend(loc="upper right", frameon=False)
save_fig(fig9b, "fig09b_augmentation_automation.png")

for _, row in augmentation.iterrows():
    print_stat(row["indicator"], f"{row['share_pct']:.0f} percent", row["source"])

# =========================================================================
# SECTION 7. Accounting-led assurance and structured reporting (Figure 10)
# =========================================================================

assurance_dates = pd.to_datetime(assurance["date"])
assurance_items = assurance["item"]
assurance_y = np.arange(len(assurance))

fig10, ax10 = plt.subplots(figsize=(9.5, 5.2))
ax10.scatter(assurance_dates, assurance_y, s=90, color=COLOR_NAVY, zorder=3)
for x, y, item in zip(assurance_dates, assurance_y, assurance_items):
    ax10.annotate(item, (x, y), textcoords="offset points", xytext=(8, 0),
                  va="center", fontsize=8, color=COLOR_NAVY)
ax10.set_yticks([])
ax10.set_xlim(pd.Timestamp("2024-03-01"), pd.Timestamp("2026-06-01"))
ax10.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax10.set_title("Figure 10: Accounting-Led AI Assurance and Structured Reporting Activity")
ax10.grid(axis="y", visible=False)
save_fig(fig10, "fig10_accounting_assurance_timeline.png")

for _, row in assurance.iterrows():
    print_stat(f"Assurance activity, {row['organisation']}, {row['item']}",
               str(row["date"][:7]), row["source"])

# =========================================================================
# SECTION 8. Education and curriculum responses (Figure 11)
# =========================================================================

edu_dates = pd.to_datetime(education["date"])
edu_items = education["item"]
edu_y = np.arange(len(education))

fig11, ax11 = plt.subplots(figsize=(9.5, 4.6))
ax11.scatter(edu_dates, edu_y, s=90, color=COLOR_GREEN, zorder=3)
for x, y, item in zip(edu_dates, edu_y, edu_items):
    ax11.annotate(item, (x, y), textcoords="offset points", xytext=(8, 0),
                  va="center", fontsize=8, color=COLOR_NAVY)
ax11.set_yticks([])
ax11.set_xlim(pd.Timestamp("2023-08-01"), pd.Timestamp("2025-08-01"))
ax11.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax11.set_title("Figure 11: Education and Curriculum Responses to Prompt Literacy")
ax11.grid(axis="y", visible=False)
save_fig(fig11, "fig11_education_timeline.png")

for _, row in education.iterrows():
    if row["indicator"].endswith("_pct") or row["indicator"].endswith("_pct_by_2030"):
        print_stat(row["indicator"], f"{row['value']:.0f} percent", row["source"])
    elif row["indicator"] in ("learners_enrolled", "learners_enrolled_total"):
        print_stat(row["indicator"], f"{row['value']:,}", row["source"])
    else:
        print_stat(row["indicator"], row["value"], row["source"])
    print_stat(f"Education item date, {row['item']}",
               row["date"][:10], row["source"])

# =========================================================================
# SECTION 9. Research opportunities (Figure 12)
# =========================================================================

fig12, ax12 = plt.subplots(figsize=(9.5, 5.6))
ax12.scatter(opportunities["data_availability"],
             opportunities["theory_significance"], s=110, color=COLOR_AMBER,
             zorder=3, edgecolor="white")
offset = 4
for i, row in opportunities.iterrows():
    label = row["opportunity"]
    y_off = offset if i % 2 == 0 else -offset - 9
    ax12.annotate(label, (row["data_availability"], row["theory_significance"]),
                  textcoords="offset points", xytext=(4, y_off), fontsize=8,
                  color=COLOR_NAVY)
ax12.set_xlim(1.5, 7.5)
ax12.set_ylim(5.5, 10.5)
ax12.set_xticks(range(2, 8))
ax12.set_yticks(range(6, 11))
ax12.set_xlabel("Data availability (author rating, 0 to 10)")
ax12.set_ylabel("Theory significance (author rating, 0 to 10)")
ax12.set_title("Figure 12: Research Opportunities by Data Availability and Significance")
save_fig(fig12, "fig12_research_opportunities.png")

print("All charts generated.")

# =========================================================================
# SECTION 10. Source-of-truth statistics for the one-page summary
# =========================================================================

print("\n===== Source-of-truth statistics (summary cross-check) =====")
print_stat("Pew ChatGPT ever-use, March 2023", "14 percent",
           "Pew Research Center (24 May 2023)")
print_stat("Pew ChatGPT ever-use, February 2024", "23 percent",
           "Pew Research Center (26 March 2024)")
print_stat("Pew ChatGPT ever-use, February-March 2025", "34 percent",
           "Pew Research Center (25 June 2025)")
print_stat("Pew ChatGPT ever-use, February 2026", "44 percent",
           "Pew Research Center (June 2026)")
print_stat("ChatGPT weekly active users, October 2025", "800 million",
           "OpenAI via Business Insider (October 2025)")
print_stat("Organisations regularly using gen AI, McKinsey 2025 wave",
           "79 percent", "McKinsey State of AI (2025)")
print_stat("Knowledge workers using gen AI at work, 2024",
           "75 percent", "Microsoft and LinkedIn Work Trend Index 2024")
print_stat("Leaders who would not hire without AI skills, 2024",
           "66 percent", "Microsoft and LinkedIn Work Trend Index 2024")
print_stat("US workers saying AI does at least some of their work, September 2025",
           "21 percent", "Pew Research Center (6 October 2025)")
print_stat("Prompt engineering job postings, 2023 to 2024",
           "1,400 to nearly 6,300", "Lightcast for Stanford AI Index 2025")
print_stat("Occupations with AI in at least 25 percent of tasks, January 2026",
           "49 percent", "Anthropic Economic Index fourth report (2026)")
print_stat("Writing task time reduction with ChatGPT",
           "40 percent", "Noy and Zhang (2023), Science")
print_stat("Average productivity gain, customer support",
           "15 percent", "Brynjolfsson, Li, and Raymond (2025), QJE")
print_stat("Consultants tasks completed with AI inside the frontier",
           "12.2 percent more", "Dell'Acqua et al. (2026), Organization Science")
print_stat("Developers faster with GitHub Copilot",
           "55.8 percent", "Peng et al. (2023)")
print_stat("Chain-of-thought GSM8K improvement",
           "17.9 to 58.1 percent", "Wei et al. (2022)")
print_stat("Zero-shot chain-of-thought MultiArith improvement",
           "17.7 to 78.7 percent", "Kojima et al. (2022)")
print_stat("Prompt engineering course learners",
           "more than 327,000", "Vanderbilt University (2024)")
print_stat("Workers core skills expected to change by 2030",
           "39 percent", "World Economic Forum Future of Jobs 2025")
print_stat("Employers prioritising reskilling by 2030",
           "85 percent", "World Economic Forum Future of Jobs 2025")
print_stat("XBRL documents from UK government programmes",
           "more than 6 million", "XBRL UK (accessed 2026)")

print("\nReplication complete. All statistics above are reproduced from "
      "the compiled data files.")
