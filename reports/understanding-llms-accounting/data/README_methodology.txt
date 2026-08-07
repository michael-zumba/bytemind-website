Understanding Large Language Models for Accounting and Finance: Data and Methodology
Dr Yuqian Zhang, Auckland University of Technology
Date: 29 July 2026

================================================================================
OVERVIEW
================================================================================

This directory contains the datasets used in the research brief "Understanding
Large Language Models and Their Implications for Accounting and Finance Research."
Each dataset is described below with its source, compilation method, and known
limitations.

================================================================================
DATASET DESCRIPTIONS
================================================================================

1. llm_parameter_timeline.csv
   Description: Parameter counts, training compute (FLOP), release dates, and
   developer information for major large language models from 2017 to 2026.
   Sources: Confirmed values from original published papers (see CSV header for
   full citations). Estimated values from industry analysis (SemiAnalysis,
   March 2023) and scaling-trend projections. Training compute values from
   Epoch AI database (epoch.ai/trends) for models through 2024; post-2024
   values projected at 4-5x per year.
   Key columns: model, release_year, release_month, parameters_billions,
   training_compute_flops, developer, notes
   Limitations: Parameter counts for proprietary models (GPT-4, Claude 3.5,
   Gemini Ultra, GPT-5, Claude 4.5, Llama 5) have not been confirmed by their
   developers. Training compute for recent models is estimated from reported
   infrastructure and training duration. FLOP values are approximate.

2. llm_arena_scores.csv
   Description: Quarterly LMArena (formerly LMSYS Chatbot Arena) Elo scores for
   selected frontier models from Q2 2023 to Q2 2026.
   Sources: LMArena public leaderboard (lmarena.ai). Scores are approximate
   quarterly means extracted from publicly available leaderboard data.
   Key columns: model, year_quarter, elo_score
   Limitations: Elo scores fluctuate with new votes and represent approximate
   quarterly snapshots. The January 2026 LMArena rebrand shifted some Elo
   distributions by 20-40 points due to methodology changes (Style Control
   filtering). Pre- and post-rebrand scores may not be directly comparable.

3. llm_hallucination_rates.csv
   Description: Hallucination rates on document summarisation benchmarks for
   major LLMs, 2024 to 2026.
   Sources: Vectara Hughes Hallucination Evaluation Model (HHEM) Leaderboard
   (github.com/vectara/hallucination-leaderboard). The HHEM benchmark measures
   factual inconsistency with a provided source document (intrinsic
   hallucination). Post-Q3 2025 values are estimated from reported trends and
   marked accordingly in the data_status column.
   Key columns: model, date_label, hallucination_rate_pct, data_status
   Limitations: Rates measure a narrow form of hallucination (consistency with
   source document). Open-ended generation shows substantially higher rates.
   These numbers are not transferable across tasks. Estimated values are
   clearly marked as such.

4. accounting_ai_adoption.csv
   Description: AI and GenAI adoption rates among accounting and tax firms,
   from industry surveys conducted in 2024 and 2025.
   Sources: Wolters Kluwer, "Future Ready Accountant Report" (2024 and 2025
   editions, wolterskluwer.com/en/know/future-ready-accountant). Thomson Reuters
   Institute, "2025 Generative AI in Professional Services Report" (2025).
   Key columns: source, year, category, percentage
   Limitations: Survey samples may not represent the entire profession. The
   Wolters Kluwer and Thomson Reuters surveys use different sampling frames
   (accounting broadly vs. tax specifically); percentages are not directly
   comparable across sources.

5. publisher_ai_policies.csv
   Description: Dates of first formal AI policy adoption by major academic
   publishers and COPE.
   Sources: Publisher websites, COPE position statements, and the Sify.ai AI
   Policies in Academic Publishing database (2025).
   Key columns: publisher, policy_date_decimal, policy_date_label
   Limitations: Policy dates are approximate (month of first issuance). Policies
   may have been updated since. Detailed provisions are summarised in the
   report; refer to original policy documents for exact wording.

6. ai_regulation_timeline.csv
   Description: Major global AI regulatory milestones from 2021 to 2026.
   Sources: European Commission, White House, NIST, Council of Europe, and
   Chinese government publications. Cross-referenced against the OECD AI
   Policy Observatory and academic reviews of AI governance.
   Key columns: date, event, jurisdiction
   Limitations: Focuses on EU, US, China, and international agreements. Does
   not include all national-level regulations. Dates for future milestones
   (2026) are per legislated timelines and may change.

7. ai_accounting_publications.csv
   Description: Estimated annual counts of AI-related publications in top-tier
   ABS 4/4* and ABDC-A* accounting and finance journals (2017-2026).
   Sources: Scopus and Web of Science keyword searches by the author. List of
   keywords and journals searched is documented in the CSV header.
   Key columns: year, methodological_empirical, conceptual_review, total
   Limitations: Keyword-based classification may misclassify papers. 2025
   counts are partial due to publication lag and indexing delays. 2026 counts
   are projected from the 2022-2025 trend. Classification into methodological
   vs. conceptual is based on abstract-level screening and is subjective.

8. big4_ai_investments.csv
   Description: Announced AI investment commitments and platform development
   by the Big Four accounting firms.
   Sources: Firm press releases and media reports (see CSV header for specific
   citations: Deloitte press release 2024; PwC press release 2024, reported in
   Financial Times Apr 2024; EY press release Sep 2023, reported in WSJ; KPMG
   press release Jun 2025).
   Key columns: firm, ai_platform, investment_usd_billions, announcement_year,
   key_initiatives
   Limitations: Investment figures are firm-announced commitments, not
   independently audited spending. Commitments may span multiple years. Platform
   capabilities are as described in announcements and may differ from deployed
   functionality.

================================================================================
DATA QUALITY AND REPRODUCIBILITY
================================================================================

All datasets were compiled manually from public sources and cross-checked
where possible. Data were verified against at least two independent sources
for major figures (regulatory dates, adoption survey results, parameter
estimates for widely-discussed models). Remaining discrepancies are noted
in the limitations for each dataset.

The Python replication script (scripts/replicate.py) loads these datasets
and reproduces all charts and statistics in the report. For data obtained
from public, open-access sources, the script reads from the CSV files
(compiled versions) because the data were assembled from multiple sources
and cannot be retrieved from a single URL. For proprietary model parameters
and training compute, the script uses the estimated values in these CSV
files and notes the estimation in chart labels.

Last updated: 29 July 2026
