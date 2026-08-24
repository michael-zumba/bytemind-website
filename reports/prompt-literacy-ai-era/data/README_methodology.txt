Prompt Literacy in the AI Era: Value, Measurement, and the Accounting Question
Data and Methodology Notes
Author: Dr Yuqian Zhang
Date: 24 August 2026

Overview
--------
This folder contains the compiled datasets behind every statistic quoted in
the research brief "Prompt Literacy in the AI Era: Value, Measurement, and
the Accounting Question" (public/reports/prompt-literacy-ai-era/index.html)
and its one-page summary (summary.html).

Files
-----
- chatgpt_adoption_us.csv: ChatGPT ever-use among US adults, Pew Research
  Center waves, March 2023 to June 2026.
- chatgpt_weekly_users.csv: ChatGPT weekly active user milestones announced
  by OpenAI, November 2023 to October 2025.
- org_genai_adoption.csv: McKinsey Global Survey on AI waves 2023, early
  2024, and 2025, with the Stanford AI Index 2025 reading as a separate
  variant.
- worker_ai_use.csv: AI use at work, Pew Research Center October 2024 and
  September 2025 waves, and Microsoft and LinkedIn Work Trend Index 2024.
- job_postings_ai_skills.csv: US job postings mentioning AI-related skills,
  Lightcast for the Stanford AI Index 2025, 2023 and 2024.
- job_share_ai_tasks.csv: Anthropic Economic Index occupation coverage and
  augmentation versus automation shares, February 2025 and January 2026.
- productivity_experiments.csv: Controlled experiments on generative AI
  productivity effects (Noy and Zhang 2023; Brynjolfsson, Li, and Raymond
  2025; Dell'Acqua et al. 2026; Peng et al. 2023).
- prompting_benchmarks.csv: Chain-of-thought and zero-shot reasoning
  benchmark results (Wei et al. 2022; Kojima et al. 2022) and PromptRobust
  adversarial-prompt statistics (Zhu et al. 2023).
- education_offerings.csv: Education and curriculum responses, including
  Vanderbilt, Google, UNESCO, and World Economic Forum items.
- ai_assurance_activity.csv: Accounting-led AI assurance and structured
  reporting activity, including IAASB, IFAC, XBRL International, and Big
  Four items.
- audit_verification_behavior.csv: Verification and error-risk evidence
  relevant to the audit mindset.
- research_opportunities.csv: Research opportunities with author ratings
  for the scatter chart.

Compilation methods
-------------------
Each CSV was compiled manually from the primary source named in the source
column, or from the cited press release or report where the primary source
publishes only PDFs or requires registration. The wave or edition of every
survey is recorded in the wave column so that survey waves are never
conflated. Where a secondary source restates a primary statistic, the
primary figure is preferred and the variant is noted.

Why auto-download is not used for most files
--------------------------------------------
The organisations that publish these statistics (Pew Research Center,
McKinsey, Microsoft and LinkedIn, Lightcast, Stanford HAI, Anthropic,
XBRL International, IAASB, IFAC) publish headline figures in PDF reports,
press releases, and article pages without stable machine-readable CSV
endpoints, and several academic papers are behind paywalls. The compiled
CSVs therefore record the values with their sources so that every number
can be traced. The replication script (scripts/replicate.py) downloads one
genuinely open dataset, the Anthropic Economic Index interaction-type CSV
from Hugging Face, with local caching, and uses it to verify the published
automation share.

Known limitations
-----------------
- Job posting counts reflect demand signals and can capture hype rather
  than verified skill requirements; they are not de-duplicated to unique
  job titles.
- Survey definitions differ across organisations (for example, "regularly
  using gen AI" in McKinsey versus "at least some of your work done with
  AI" in Pew), so cross-survey comparisons are indicative only.
- The accounting-as-language thesis is treated as a hypothesis. Several
  rows in ai_assurance_activity.csv document standard-setting and firm
  activity rather than measured performance differences, and the Big Four
  launch items are media-reported.
- Research opportunity ratings in research_opportunities.csv are the
  author's analytical assessment, not survey or experimental measurements.

License and attribution
-----------------------
Compiled data are provided for open access under the same terms as the
report. Please cite: Zhang, Y. (2026). Prompt Literacy and the New Language
of the AI Era. Available at https://zhangyuqian.com/prompt-literacy-ai-era/.
