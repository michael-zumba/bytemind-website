#!/usr/bin/env python3
"""
Generative AI and Everyday Life: Wellbeing, Work, and Skills Before and After
ChatGPT (2015-2026)
Replication Script

Author: Dr Yuqian Zhang
Date: 23 August 2026

Description: This script reproduces every chart and statistic in the research
brief from the source data files. It generates 17 figures matching the ECharts
visualisations in the report and prints the summary statistics quoted in the
one-page summary.

Data sources:
- Compiled CSV files in the ../data/ directory. These are manually compiled
  from published reports (Gallup Global Emotions, Gallup State of the Global
  Workplace, Pew Research Center, Microsoft Work Trend Index, ILO, IMF, OECD,
  McKinsey, World Economic Forum) and peer-reviewed studies (Noy and Zhang
  2023; Peng et al. 2023; Brynjolfsson, Li, and Raymond 2025; Cui et al. 2026;
  Dell'Acqua et al. 2023; Otis et al. 2024; Bastani et al. 2024). They cannot
  be auto-downloaded because the underlying organisations publish headline
  statistics in PDF reports and press releases without stable CSV endpoints,
  and several academic papers are behind paywalls.
- The World Happiness Report 2026 Figure 2.1 data file is openly downloadable
  and is fetched automatically with local caching (see Section 2).
"""

# === Dependencies (pinned) ===
# Install with:
#   pip install --break-system-packages matplotlib==3.9.1 numpy==2.0.1 pandas==2.2.2 openpyxl==3.1.5
import os
import ssl
import sys
import urllib.request
import warnings

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
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

# Colour palette consistent with the report
C_NAVY = "#1e3a5f"
C_BLUE = "#3b6e9e"
C_LIGHT = "#7ba3cc"
C_RED = "#c0392b"
C_GREEN = "#27ae60"
C_AMBER = "#f39c12"
C_GREY = "#7f8c8d"


# === Helpers ===
def load_csv(name):
    """Load a CSV from ../data/, skipping comment lines starting with #."""
    path = os.path.join(DATA_DIR, name)
    if not os.path.exists(path):
        sys.exit("ERROR: Missing data file: " + path)
    with open(path, "r", encoding="utf-8") as fh:
        lines = [ln for ln in fh if not ln.lstrip().startswith("#")]
    if not lines:
        sys.exit("ERROR: Data file contains no data rows: " + path)
    import io
    df = pd.read_csv(io.StringIO("".join(lines)))
    return df


def check_columns(df, name, cols):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        sys.exit("ERROR: " + name + " missing columns: " + ", ".join(missing))


def save_fig(fig, name):
    path = os.path.join(CHARTS_DIR, name)
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("Saved " + name)


# ============================================================================
# SECTION 1: TIMELINE OF GENERATIVE AI MILESTONES (Figure 1)
# ============================================================================
# Compiled from public announcements; cannot be auto-downloaded.
df_milestones = load_csv("ai_era_milestones.csv")
check_columns(df_milestones, "ai_era_milestones.csv", ["date", "milestone", "category"])
df_milestones["date"] = pd.to_datetime(df_milestones["date"])
df_milestones = df_milestones.sort_values("date")

fig, ax = plt.subplots(figsize=(11, 5.2))
colors = {
    "Inflection point": C_RED,
    "Model milestone": C_NAVY,
    "Consumer product": C_BLUE,
    "Adoption": C_GREEN,
    "Regulation": C_AMBER,
    "Research": C_GREY,
    "Society": C_GREY,
}
ypos = np.arange(len(df_milestones))
for i, row in df_milestones.iterrows():
    ax.scatter(row["date"], i, s=90, color=colors.get(row["category"], C_GREY),
               edgecolor="white", zorder=3)
    ax.annotate(row["milestone"], (row["date"], i),
                textcoords="offset points", xytext=(6, 3), fontsize=7.5)
ax.axvline(pd.Timestamp("2022-11-30"), color=C_RED, linestyle="--", linewidth=1.2)
ax.text(pd.Timestamp("2022-11-30"), len(df_milestones) - 1.2, "ChatGPT launch",
        color=C_RED, fontsize=9, fontweight="bold")
ax.set_yticks([])
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.set_title("Figure 1: Generative AI Milestones and the ChatGPT Inflection Point (2016-2026)")
ax.set_xlabel("Year")
ax.grid(axis="x", alpha=0.3)
fig.tight_layout()
save_fig(fig, "fig01_milestones_timeline.png")


# ============================================================================
# SECTION 2: QUALITY OF LIFE AND LIFE SATISFACTION (Figure 2)
# ============================================================================
# The World Happiness Report 2026 data file is public and auto-downloaded with
# local caching. If the download fails, fall back to the compiled CSV.
WHR_URL = "https://files.worldhappiness.report/WHR26_Data_Figure_2.1.xlsx"
WHR_CACHE = os.path.join(CACHE_DIR, "WHR26_Data_Figure_2.1.xlsx")


def download_whr():
    if os.path.exists(WHR_CACHE):
        return WHR_CACHE
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    }
    try:
        print("Downloading World Happiness Report 2026 data file...")
        req = urllib.request.Request(WHR_URL, headers=headers)
        with urllib.request.urlopen(req, timeout=120) as resp:
            with open(WHR_CACHE, "wb") as fh:
                fh.write(resp.read())
        return WHR_CACHE
    except Exception:
        # Some environments (notably macOS system Python) lack the CA bundle
        # needed for certificate verification. Retry without verification so
        # the public data file can still be fetched.
        print("Certificate verification failed; retrying without verification.")
        try:
            ctx = ssl._create_unverified_context()
            req = urllib.request.Request(WHR_URL, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=120) as resp:
                with open(WHR_CACHE, "wb") as fh:
                    fh.write(resp.read())
            return WHR_CACHE
        except Exception as exc:
            print("WARNING: Could not download WHR file (" + str(exc) + "); using compiled CSV.")
            return None


def compute_life_satisfaction():
    xlsx_path = download_whr()
    if xlsx_path:
        try:
            raw = pd.read_excel(xlsx_path, sheet_name=0)
            raw.columns = [str(c).strip() for c in raw.columns]
            raw = raw.rename(columns={
                "Year": "year",
                "Country name": "country",
                "Life evaluation (3-year average)": "ladder",
            })
            out = raw.groupby("year")["ladder"].agg(["mean", "count"]).reset_index()
            out.columns = ["year", "global_mean", "n_countries"]
            for country in ["United States", "United Kingdom", "Japan", "Australia"]:
                sub = raw[raw["country"] == country][["year", "ladder"]]
                sub = sub.rename(columns={"ladder": country.lower().replace(" ", "_")})
                out = out.merge(sub, on="year", how="left")
            return out.round(3)
        except Exception as exc:
            print("WARNING: Could not parse WHR file (" + str(exc) + "); using compiled CSV.")
    df = load_csv("ai_era_life_satisfaction.csv")
    check_columns(df, "ai_era_life_satisfaction.csv",
                  ["year", "global_mean", "n_countries", "united_states",
                   "united_kingdom", "japan", "australia"])
    return df


df_life = compute_life_satisfaction()

fig, ax = plt.subplots(figsize=(11, 5.4))
ax.plot(df_life["year"], df_life["global_mean"], marker="o", linewidth=2.5,
        color=C_NAVY, label="World (unweighted country mean)")
for col, label, color in [
    ("united_states", "United States", C_RED),
    ("united_kingdom", "United Kingdom", C_GREEN),
    ("japan", "Japan", C_AMBER),
    ("australia", "Australia", C_BLUE),
]:
    ax.plot(df_life["year"], df_life[col], marker="s", markersize=4,
            linewidth=1.6, color=color, label=label)
ax.axvline(2022.9, color=C_RED, linestyle="--", linewidth=1.2)
ax.annotate("ChatGPT launch\n(Nov 2022)", xy=(2022.9, 4.6), xytext=(2020.2, 4.35),
            fontsize=8.5, color=C_RED)
ax.set_title("Figure 2: Life Evaluation Before and After ChatGPT (2011-2025)")
ax.set_ylabel("Cantril ladder, 0-10 (3-year averages)")
ax.set_xlabel("Report year")
ax.legend(fontsize=8, ncol=2, loc="lower right")
ax.grid(alpha=0.3)
ax.set_ylim(3.9, 7.8)
fig.tight_layout()
save_fig(fig, "fig02_life_satisfaction.png")

pre_mean = df_life[(df_life["year"] >= 2015) & (df_life["year"] <= 2022)]["global_mean"].mean()
post_mean = df_life[(df_life["year"] >= 2023) & (df_life["year"] <= 2025)]["global_mean"].mean()


# ============================================================================
# SECTION 3: HAPPINESS AND AFFECTIVE WELLBEING (Figure 3)
# ============================================================================
df_affect = load_csv("ai_era_affect_indices.csv")
check_columns(df_affect, "ai_era_affect_indices.csv",
              ["year", "positive_experience_index", "negative_experience_index"])

fig, ax = plt.subplots(figsize=(11, 5))
ax.plot(df_affect["year"], df_affect["positive_experience_index"], marker="o",
        linewidth=2.5, color=C_GREEN, label="Positive Experience Index")
ax.plot(df_affect["year"], df_affect["negative_experience_index"], marker="o",
        linewidth=2.5, color=C_RED, label="Negative Experience Index")
ax.axvline(2022.9, color=C_RED, linestyle="--", linewidth=1.2)
ax.annotate("ChatGPT launch\n(Nov 2022)", xy=(2022.9, 31), xytext=(2017.8, 25),
            fontsize=8.5, color=C_RED)
ax.set_title("Figure 3: Global Positive and Negative Experience (2015-2024)")
ax.set_ylabel("Index score, 0-100")
ax.set_xlabel("Survey year")
ax.set_ylim(20, 80)
ax.legend(fontsize=9)
ax.grid(alpha=0.3)
fig.tight_layout()
save_fig(fig, "fig03_affect_indices.png")


# ============================================================================
# SECTION 4: PERCEIVED FREEDOM AND AUTONOMY (Figure 4)
# ============================================================================
df_freedom = load_csv("ai_era_freedom_satisfaction.csv")
check_columns(df_freedom, "ai_era_freedom_satisfaction.csv",
              ["year", "series", "value_pct"])
us_women = df_freedom[df_freedom["series"] == "us_women"]
world = df_freedom[df_freedom["series"] == "world_median"]

fig, ax = plt.subplots(figsize=(11, 5))
ax.bar(world["year"], world["value_pct"], width=0.7, color=C_LIGHT,
       label="World median / average (Gallup)", alpha=0.85)
ax.plot(us_women["year"], us_women["value_pct"], marker="o", linewidth=2.4,
        color=C_NAVY, label="United States, women (Gallup)")
ax.axvline(2022.9, color=C_RED, linestyle="--", linewidth=1.2)
ax.annotate("ChatGPT launch\n(Nov 2022)", xy=(2022.9, 74), xytext=(2018.2, 60),
            fontsize=8.5, color=C_RED)
ax.set_title("Figure 4: Satisfaction With Personal Freedom (Gallup World Poll)")
ax.set_ylabel("Share satisfied with freedom to choose what to do with life (%)")
ax.set_xlabel("Year")
ax.set_ylim(50, 100)
ax.legend(fontsize=9)
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
save_fig(fig, "fig04_freedom_satisfaction.png")


# ============================================================================
# SECTION 5: STRESS AND MENTAL HEALTH (Figure 5)
# ============================================================================
df_stress = load_csv("ai_era_stress.csv")
check_columns(df_stress, "ai_era_stress.csv",
              ["year", "population_stress_pct", "workplace_stress_pct"])

fig, ax = plt.subplots(figsize=(11, 5))
ax.plot(df_stress["year"], df_stress["population_stress_pct"], marker="o",
        linewidth=2.4, color=C_BLUE, label="All adults (Gallup Global Emotions)")
ax.plot(df_stress["year"], df_stress["workplace_stress_pct"], marker="s",
        linewidth=2.4, color=C_RED, label="Employees (Gallup State of the Global Workplace)")
ax.axvline(2022.9, color=C_RED, linestyle="--", linewidth=1.2)
ax.annotate("ChatGPT launch\n(Nov 2022)", xy=(2022.9, 42.5), xytext=(2018.4, 44.5),
            fontsize=8.5, color=C_RED)
ax.set_title("Figure 5: Self-Reported Daily Stress Worldwide (2017-2024)")
ax.set_ylabel("Share experiencing a lot of stress (%)")
ax.set_xlabel("Survey year")
ax.set_ylim(30, 50)
ax.legend(fontsize=9)
ax.grid(alpha=0.3)
fig.tight_layout()
save_fig(fig, "fig05_stress.png")


# ============================================================================
# SECTION 6: CONSUMER ADOPTION OF GENERATIVE AI (Figures 6a and 6b)
# ============================================================================
df_chatgpt = load_csv("ai_era_ai_adoption_chatgpt.csv")
check_columns(df_chatgpt, "ai_era_ai_adoption_chatgpt.csv", ["date", "metric", "value"])
df_chatgpt["date"] = pd.to_datetime(df_chatgpt["date"])
weekly = df_chatgpt[df_chatgpt["metric"] == "weekly_active_users_millions"]

fig, ax = plt.subplots(figsize=(8.5, 4.8))
ax.fill_between(weekly["date"], weekly["value"], color=C_NAVY, alpha=0.25)
ax.plot(weekly["date"], weekly["value"], marker="o", linewidth=2.5, color=C_NAVY)
for _, row in weekly.iterrows():
    ax.annotate(str(int(row["value"])) + "M", (row["date"], row["value"]),
                textcoords="offset points", xytext=(0, 8), fontsize=9,
                ha="center", color=C_NAVY)
ax.set_title("Figure 12a: ChatGPT Weekly Active Users (millions)")
ax.set_ylabel("Weekly active users (millions)")
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax.grid(alpha=0.3)
fig.tight_layout()
save_fig(fig, "fig06a_chatgpt_users.png")

df_pew = load_csv("ai_era_ai_adoption_pew.csv")
check_columns(df_pew, "ai_era_ai_adoption_pew.csv", ["year", "age_group", "share_pct"])
pew_all = df_pew[df_pew["age_group"] == "All adults"].sort_values("year")

fig, ax = plt.subplots(figsize=(8.5, 4.8))
bars = ax.bar(pew_all["year"].astype(str), pew_all["share_pct"], color=C_BLUE, width=0.55)
for b, v in zip(bars, pew_all["share_pct"]):
    ax.text(b.get_x() + b.get_width() / 2, v + 1, str(int(v)) + "%",
            ha="center", fontsize=9)
ax.set_title("Figure 12b: US Adults Who Have Ever Used ChatGPT (Pew Research Center)")
ax.set_ylabel("Share of US adults (%)")
ax.set_ylim(0, 55)
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
save_fig(fig, "fig06b_pew_usage.png")


# ============================================================================
# SECTION 7: ORGANISATIONAL ADOPTION (Figure 7)
# ============================================================================
df_org = load_csv("ai_era_ai_adoption_orgs.csv")
check_columns(df_org, "ai_era_ai_adoption_orgs.csv",
              ["year", "ai_use_pct", "genai_use_pct"])

fig, ax = plt.subplots(figsize=(10, 5))
x = np.arange(len(df_org))
w = 0.36
b1 = ax.bar(x - w / 2, df_org["ai_use_pct"], w, color=C_NAVY, label="AI in at least one function")
b2 = ax.bar(x + w / 2, df_org["genai_use_pct"], w, color=C_AMBER, label="Generative AI regularly")
for bars, vals in [(b1, df_org["ai_use_pct"]), (b2, df_org["genai_use_pct"])]:
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1, str(int(v)) + "%",
                ha="center", fontsize=9)
ax.set_xticks(x)
ax.set_xticklabels(df_org["year"])
ax.set_title("Figure 13: Organisational AI Adoption (McKinsey State of AI)")
ax.set_ylabel("Share of surveyed organisations (%)")
ax.set_ylim(0, 100)
ax.legend(fontsize=9)
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
save_fig(fig, "fig07_organisational_adoption.png")


# ============================================================================
# SECTION 8: OCCUPATIONAL EXPOSURE ESTIMATES (Figure 8)
# ============================================================================
df_exposure = load_csv("ai_era_ai_exposure.csv")
check_columns(df_exposure, "ai_era_ai_exposure.csv",
              ["study", "scope", "measure", "value_pct"])
df_exp = df_exposure.copy()
df_exp["label"] = (df_exp["study"] + " | " + df_exp["scope"] + ": " + df_exp["measure"])
df_exp = df_exp.sort_values("value_pct")

fig, ax = plt.subplots(figsize=(11, 7.5))
cols = [C_NAVY if s in ("ILO",) else C_BLUE if s == "IMF" else C_GREEN if s == "OECD" else C_GREY
        for s in df_exp["study"]]
bars = ax.barh(df_exp["label"], df_exp["value_pct"], color=cols)
for b, v in zip(bars, df_exp["value_pct"]):
    ax.text(v + 0.8, b.get_y() + b.get_height() / 2, str(v) + "%",
            va="center", fontsize=8)
ax.set_title("Figure 7: Estimates of AI Exposure Across Studies and Definitions")
ax.set_xlabel("Share of employment or tasks (%)")
ax.set_xlim(0, 80)
ax.grid(axis="x", alpha=0.3)
ax.tick_params(axis="y", labelsize=8)
fig.tight_layout()
save_fig(fig, "fig08_exposure_estimates.png")


# ============================================================================
# SECTION 9: PERCEIVED JOB SECURITY (Figures 9a and 9b)
# ============================================================================
df_job = load_csv("ai_era_job_security_perceived.csv")
check_columns(df_job, "ai_era_job_security_perceived.csv",
              ["survey", "indicator", "value_pct"])

worried = df_job[df_job["indicator"].str.contains("worry|worried", case=False)]
worried = worried.sort_values("value_pct")
fig, ax = plt.subplots(figsize=(8.5, 4.8))
labels = [
    "Gallup 2021: tech\nmakes job obsolete",
    "Gallup 2023: tech\nmakes job obsolete",
    "Microsoft 2023: AI\nwill replace my job",
    "Pew 2025: worried\nabout AI at work",
]
vals = worried["value_pct"].tolist()
bars = ax.bar(labels, vals, color=[C_GREY, C_BLUE, C_AMBER, C_RED])
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width() / 2, v + 1, str(int(v)) + "%",
            ha="center", fontsize=9)
ax.set_title("Figure 6a: Workers Who Worry About AI and Their Jobs")
ax.set_ylabel("Share of workers (%)")
ax.set_ylim(0, 65)
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
save_fig(fig, "fig09a_job_worries.png")

sentiments = df_job[df_job["survey"] == "Pew Research Center"]
sentiments = sentiments[sentiments["indicator"].str.contains(
    "worried|hopeful|overwhelmed|excited", case=False)]
sentiments = sentiments.sort_values("value_pct", ascending=False)
fig, ax = plt.subplots(figsize=(8.5, 4.8))
cols_map = {"worried": C_RED, "overwhelmed": C_AMBER, "hopeful": C_GREEN, "excited": C_BLUE}
label_map = {"worried": "Worried", "overwhelmed": "Overwhelmed",
             "hopeful": "Hopeful", "excited": "Excited"}
labels2 = [label_map.get(s.split()[1].strip(",").lower(), "Other")
           for s in sentiments["indicator"]]
colors2 = [cols_map.get(l.lower(), C_GREY) for l in labels2]
bars = ax.bar(labels2, sentiments["value_pct"], color=colors2)
for b, v in zip(bars, sentiments["value_pct"]):
    ax.text(b.get_x() + b.get_width() / 2, v + 1, str(int(v)) + "%",
            ha="center", fontsize=9)
ax.set_title("Figure 6b: How US Workers Feel About AI in the Workplace (Pew, Feb 2025)")
ax.set_ylabel("Share of US workers (%)")
ax.set_ylim(0, 65)
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
save_fig(fig, "fig09b_pew_sentiment.png")


# ============================================================================
# SECTION 10: DISTRIBUTION OF EFFECTS (Figures 10a and 10b)
# ============================================================================
df_dist = load_csv("ai_era_distribution.csv")
check_columns(df_dist, "ai_era_distribution.csv", ["group", "measure", "value_pct"])

age_order = ["18-29", "30-49", "50-64", "65+"]
age_usage = df_dist[df_dist["measure"].str.contains("used ChatGPT")].copy()
age_usage["order"] = age_usage["group"].map({g: i for i, g in enumerate(age_order)})
age_usage = age_usage.sort_values("order")
fig, ax = plt.subplots(figsize=(8.5, 4.8))
bars = ax.bar(age_usage["group"], age_usage["value_pct"], color=C_NAVY)
for b, v in zip(bars, age_usage["value_pct"]):
    ax.text(b.get_x() + b.get_width() / 2, v + 1, str(int(v)) + "%",
            ha="center", fontsize=9)
ax.set_title("Figure 9a: US Adults Who Have Used ChatGPT by Age (Pew, 2025)")
ax.set_ylabel("Share of age group (%)")
ax.set_ylim(0, 70)
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
save_fig(fig, "fig10a_age_usage.png")

exposure_groups = df_dist[df_dist["measure"].str.contains("exposed|automatable")]
fig, ax = plt.subplots(figsize=(9.5, 6))
exp2 = exposure_groups.sort_values("value_pct")
colors3 = []
for _, r in exp2.iterrows():
    if "Advanced" in r["group"]:
        colors3.append(C_NAVY)
    elif "Emerging" in r["group"] or "Low-income" in r["group"]:
        colors3.append(C_BLUE)
    elif "Women" in r["group"] or "Female" in r["group"]:
        colors3.append(C_RED)
    elif "Men" in r["group"] or "Male" in r["group"]:
        colors3.append(C_AMBER)
    else:
        colors3.append(C_GREY)
bars = ax.barh(exp2["group"], exp2["value_pct"], color=colors3)
for b, v in zip(bars, exp2["value_pct"]):
    ax.text(v + 0.5, b.get_y() + b.get_height() / 2, str(v) + "%",
            va="center", fontsize=8)
ax.set_title("Figure 9b: AI Exposure by Group (ILO, IMF, OECD)")
ax.set_xlabel("Share of employment or occupations (%)")
ax.set_xlim(0, 70)
ax.grid(axis="x", alpha=0.3)
fig.tight_layout()
save_fig(fig, "fig10b_exposure_groups.png")


# ============================================================================
# SECTION 11: NON-EXPERT EMPOWERMENT AND PRODUCTIVITY (Figure 11)
# ============================================================================
df_prod = load_csv("ai_era_productivity_evidence.csv")
check_columns(df_prod, "ai_era_productivity_evidence.csv",
              ["study", "outcome_metric", "effect_pct", "skill_group"])
df_prod = df_prod.sort_values("effect_pct")

fig, ax = plt.subplots(figsize=(12, 7))
colors4 = [C_RED if v < 0 else C_GREEN if "quality" in m.lower() else C_NAVY
           for v, m in zip(df_prod["effect_pct"], df_prod["outcome_metric"])]
bars = ax.barh(range(len(df_prod)), df_prod["effect_pct"], color=colors4)
ax.set_yticks(range(len(df_prod)))
ax.set_yticklabels(
    [s + " (" + m + ")" for s, m in zip(df_prod["study"], df_prod["outcome_metric"])],
    fontsize=8)
for b, v in zip(bars, df_prod["effect_pct"]):
    ax.text(v + (0.8 if v >= 0 else -0.8), b.get_y() + b.get_height() / 2,
            ("+" if v > 0 else "") + str(v) + "%",
            va="center", ha="left" if v >= 0 else "right", fontsize=8)
ax.axvline(0, color="#44403c", linewidth=1)
ax.set_title("Figure 10: Experimental Evidence on Generative AI and Productivity")
ax.set_xlabel("Effect size (%)")
ax.grid(axis="x", alpha=0.3)
fig.tight_layout()
save_fig(fig, "fig11_productivity_evidence.png")


# ============================================================================
# SECTION 12: LEARNING AND DESKILLING EVIDENCE (Figure 12)
# ============================================================================
df_learn = load_csv("ai_era_learning_evidence.csv")
check_columns(df_learn, "ai_era_learning_evidence.csv",
              ["condition", "practice_performance_change_pct",
               "exam_without_access_change_pct"])

fig, ax = plt.subplots(figsize=(10, 5))
labels3 = df_learn["condition"].tolist()
practice = df_learn["practice_performance_change_pct"].tolist()
exam = df_learn["exam_without_access_change_pct"].tolist()
x = np.arange(len(labels3))
w = 0.36
b1 = ax.bar(x - w / 2, practice, w, color=C_GREEN, label="Practice problems with AI access")
b2 = ax.bar(x + w / 2, exam, w, color=C_RED, label="Exam without AI access")
for bars, vals in [(b1, practice), (b2, exam)]:
    for b, v in zip(bars, vals):
        if pd.isna(v):
            continue
        ax.text(b.get_x() + b.get_width() / 2, v + (2 if v >= 0 else -4),
                ("+" if v > 0 else "") + str(int(v)) + "%",
                ha="center", fontsize=9)
ax.set_xticks(x)
ax.set_xticklabels([l.replace(" (", "\n(") for l in labels3], fontsize=8.5)
ax.axhline(0, color="#44403c", linewidth=0.8)
ax.set_title("Figure 11: Generative AI Can Raise Practice Performance but Reduce Learning (Bastani et al.)")
ax.set_ylabel("Change relative to control (%)")
ax.legend(fontsize=9)
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
save_fig(fig, "fig12_learning_evidence.png")


# ============================================================================
# SECTION 13: JOB TRANSFORMATION PROJECTIONS (Figure 13)
# ============================================================================
df_jobs = load_csv("ai_era_job_transformation.csv")
check_columns(df_jobs, "ai_era_job_transformation.csv",
              ["report_year", "jobs_created_millions", "jobs_eliminated_millions",
               "net_millions"])

fig, ax = plt.subplots(figsize=(10, 5))
x = np.arange(len(df_jobs))
w = 0.26
b1 = ax.bar(x - w, df_jobs["jobs_created_millions"], w, color=C_GREEN, label="Jobs created (projected)")
b2 = ax.bar(x, df_jobs["jobs_eliminated_millions"], w, color=C_RED, label="Jobs displaced (projected)")
b3 = ax.bar(x + w, df_jobs["net_millions"], w, color=C_NAVY, label="Net change (projected)")
for bars, vals in [(b1, df_jobs["jobs_created_millions"]),
                   (b2, df_jobs["jobs_eliminated_millions"]),
                   (b3, df_jobs["net_millions"])]:
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 2,
                ("+" if v > 0 else "") + str(int(v)) + "M", ha="center", fontsize=9)
ax.set_xticks(x)
ax.set_xticklabels(["WEF 2023\n(2023-2027)", "WEF 2025\n(2025-2030)"])
ax.axhline(0, color="#44403c", linewidth=0.8)
ax.set_title("Figure 8: Projected Job Creation and Displacement (WEF Future of Jobs)")
ax.set_ylabel("Millions of jobs")
ax.legend(fontsize=9)
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
save_fig(fig, "fig13_job_transformation.png")


# ============================================================================
# SECTION 14: RESEARCH OPPORTUNITIES (Figure 14)
# ============================================================================
df_research = load_csv("ai_era_research_opportunities.csv")
check_columns(df_research, "ai_era_research_opportunities.csv",
              ["topic", "data_availability", "theoretical_significance"])

fig, ax = plt.subplots(figsize=(10, 6))
sc = ax.scatter(df_research["data_availability"], df_research["theoretical_significance"],
                s=220, color=C_NAVY, alpha=0.75, edgecolor="white")
for i, (_, row) in enumerate(df_research.iterrows()):
    dy = 9 if i % 2 == 0 else -18
    ax.annotate(row["topic"], (row["data_availability"], row["theoretical_significance"]),
                textcoords="offset points", xytext=(6, dy), fontsize=8.5)
ax.set_xlim(3, 9)
ax.set_ylim(6, 11)
ax.set_title("Figure 14: Research Opportunities by Data Availability and Theoretical Significance")
ax.set_xlabel("Data availability (author assessment, 0-10)")
ax.set_ylabel("Theoretical significance (author assessment, 0-10)")
ax.grid(alpha=0.3)
fig.tight_layout()
save_fig(fig, "fig14_research_opportunities.png")


# ============================================================================
# KEY STATISTICS (reproduced for the report and one-page summary)
# ============================================================================
print("\n=== KEY STATISTICS (as quoted in report and summary) ===")
print("Life ladder: world mean 2015 = %.3f; 2025 = %.3f; pre-AI mean 2015-2022 = %.3f; post-AI mean 2023-2025 = %.3f"
      % (df_life[df_life["year"] == 2015]["global_mean"].iloc[0],
         df_life[df_life["year"] == 2025]["global_mean"].iloc[0], pre_mean, post_mean))
pe_2021 = df_affect[df_affect["year"] == 2021]["positive_experience_index"].iloc[0]
pe_2024 = df_affect[df_affect["year"] == 2024]["positive_experience_index"].iloc[0]
ne_2021 = df_affect[df_affect["year"] == 2021]["negative_experience_index"].iloc[0]
ne_2024 = df_affect[df_affect["year"] == 2024]["negative_experience_index"].iloc[0]
stress_2021 = df_affect[df_affect["year"] == 2021]["stress_pct"].iloc[0]
stress_2024 = df_affect[df_affect["year"] == 2024]["stress_pct"].iloc[0]
print("Positive Experience Index: 2021 = %.0f; 2024 = %.0f" % (pe_2021, pe_2024))
print("Negative Experience Index: 2021 = %.0f; 2024 = %.0f" % (ne_2021, ne_2024))
print("Population stress: 2021 = %.0f%%; 2024 = %.0f%%" % (stress_2021, stress_2024))
ws = df_stress[df_stress["year"] == 2024]["workplace_stress_pct"].iloc[0]
print("Workplace stress 2024 = %.0f%%" % ws)
us_women_2024 = us_women[us_women["year"] == 2024]["value_pct"].iloc[0]
world_2025 = world[world["year"] == 2025]["value_pct"].iloc[0]
print("Freedom satisfaction: US women 2024 = %.0f%%; world median 2025 = %.0f%%" % (us_women_2024, world_2025))
chatgpt_latest = weekly["value"].max()
print("ChatGPT weekly active users (latest) = %.0f million" % chatgpt_latest)
pew_2026 = pew_all[pew_all["year"] == 2026]["share_pct"].iloc[0]
pew_young = age_usage[age_usage["group"] == "18-29"]["value_pct"].iloc[0]
print("Pew ChatGPT use: 2026 = %.0f%%; 18-29 in 2025 = %.0f%%" % (pew_2026, pew_young))
ai88 = df_org[df_org["year"] == 2025]["ai_use_pct"].iloc[0]
gen79 = df_org[df_org["year"] == 2025]["genai_use_pct"].iloc[0]
print("Organisations 2025: AI use = %.0f%%; gen AI = %.0f%%" % (ai88, gen79))
ilo55 = df_exposure[(df_exposure["study"] == "ILO") & (df_exposure["scope"] == "High-income countries") &
                    (df_exposure["measure"].str.contains("highly exposed"))]["value_pct"].iloc[0]
imf60 = df_exposure[(df_exposure["study"] == "IMF") & (df_exposure["scope"] == "Advanced economies")]["value_pct"].iloc[0]
imf40 = df_exposure[(df_exposure["study"] == "IMF") & (df_exposure["scope"] == "World")]["value_pct"].iloc[0]
oecd26 = df_exposure[(df_exposure["study"] == "OECD") & (df_exposure["scope"] == "OECD average") &
                     (df_exposure["measure"].str.contains("currently exposed"))]["value_pct"].iloc[0]
print("Exposure: ILO high-income highly exposed = %.1f%%; IMF world = %.0f%%; IMF advanced = %.0f%%; OECD current = %.0f%%"
      % (ilo55, imf40, imf60, oecd26))
worried_pew = worried[worried["survey"] == "Pew Research Center"]["value_pct"].iloc[0]
worried_msft = worried[worried["survey"] == "Microsoft Work Trend Index"]["value_pct"].iloc[0]
print("Job worries: Pew 2025 = %.0f%%; Microsoft 2023 = %.0f%%" % (worried_pew, worried_msft))
noy40 = df_prod[(df_prod["study"] == "Noy and Zhang") & (df_prod["outcome_metric"].str.contains("Time"))]["effect_pct"].iloc[0]
bryn14 = df_prod[(df_prod["study"] == "Brynjolfsson Li and Raymond") & (df_prod["skill_group"] == "All agents")]["effect_pct"].iloc[0]
bryn34 = df_prod[(df_prod["study"] == "Brynjolfsson Li and Raymond") & (df_prod["skill_group"].str.contains("Novice"))]["effect_pct"].iloc[0]
cui26 = df_prod[(df_prod["study"] == "Cui et al.")]["effect_pct"].iloc[0]
print("Productivity: Noy & Zhang speed = %.0f%%; Brynjolfsson avg = %.0f%%; novice = %.0f%%; Cui et al. tasks = %.1f%%"
      % (noy40, bryn14, bryn34, cui26))
created25 = df_jobs[df_jobs["report_year"] == 2025]["jobs_created_millions"].iloc[0]
elim25 = df_jobs[df_jobs["report_year"] == 2025]["jobs_eliminated_millions"].iloc[0]
net25 = df_jobs[df_jobs["report_year"] == 2025]["net_millions"].iloc[0]
churn23 = df_jobs[df_jobs["report_year"] == 2023]["job_churn_pct"].iloc[0]
print("WEF 2025 projections: created = %.0fM; displaced = %.0fM; net = %.0fM; WEF 2023 churn = %.0f%%"
      % (created25, elim25, net25, churn23))
print("Bastani practice GPT Base = %.0f%%; exam without access = %.0f%%"
      % (df_learn["practice_performance_change_pct"].iloc[0],
         df_learn["exam_without_access_change_pct"].iloc[0]))

print("\nAll figures saved to " + CHARTS_DIR)
