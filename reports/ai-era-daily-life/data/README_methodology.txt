Generative AI and Everyday Life: Wellbeing, Work, and Skills Before and After
ChatGPT (2015-2026)
Data and Methodology
Dr Yuqian Zhang, Auckland University of Technology
Date: 23 August 2026

================================================================================
OVERVIEW
================================================================================

This directory contains the datasets used in the research brief "Generative AI
and Everyday Life." The brief compares the pre-AI era (2015 to 2022) with the
post-AI era (2023 to 2026) across seven dimensions: quality of life, happiness
and affective wellbeing, perceived freedom, stress and mental health, job
security, the distribution of effects, and the question of whether generative
AI lets non-experts perform work once reserved for specialists.

Each CSV begins with comment lines (lines starting with #) that document the
variables and sources. All values were verified against the primary or
authoritative source listed before inclusion. Where a figure is approximate
because the source itself is approximate (for example, the ILO's "nearly a
quarter" of clerical tasks), the CSV and the report say so explicitly.

================================================================================
WHY MOST FILES ARE NOT AUTO-DOWNLOADED
================================================================================

The replication script reads most files from this directory instead of
downloading them, for three reasons:

1. Gallup, Pew, McKinsey, and the World Economic Forum publish their headline
   statistics in reports and press releases rather than as structured,
   machine-readable files with stable URLs.
2. The ILO, IMF, and OECD publish the underlying microdata behind restricted
   access or through interactive platforms that do not expose stable CSV URLs.
3. The experimental results (Noy and Zhang, Peng et al., Brynjolfsson et al.,
   Cui et al., Dell'Acqua et al., Otis et al., Bastani et al.) are reported
   in journal articles and working papers, some behind paywalls.

The one file that is openly downloadable, the World Happiness Report 2026
Figure 2.1 data file, is auto-downloaded by the replication script with local
caching. The life satisfaction series in ai_era_life_satisfaction.csv is
derived from that file by computing the unweighted mean of the country-level
life evaluation across all countries with data in each report year.

================================================================================
DATASET DESCRIPTIONS
================================================================================

1. ai_era_milestones.csv
   Description: Public milestones in the development and diffusion of
   generative AI, 2016 to 2026, including the ChatGPT launch in November 2022
   used as the inflection point in the report.
   Sources: Company announcements (OpenAI, Google, Microsoft, DeepMind,
   Stability AI, GitHub, DeepSeek), published papers (Vaswani et al. 2017;
   Radford et al. 2018; Devlin et al. 2018; Brown et al. 2020), the European
   Union, and the Nobel Foundation.
   Limitations: Dates are public announcement or release dates. Some model
   releases have both preprint and public launch dates; this file uses the
   public launch date.

2. ai_era_life_satisfaction.csv
   Description: Cantril ladder life evaluation (0 to 10) for the world and for
   four selected economies (United States, United Kingdom, Japan, Australia),
   2011 to 2025. Values are the 3-year rolling averages published by the World
   Happiness Report; for example, the 2025 row averages 2023 to 2025.
   Sources: World Happiness Report 2026, Data for Figure 2.1
   (files.worldhappiness.report/WHR26_Data_Figure_2.1.xlsx).
   Compilation: global_mean is the unweighted mean across all countries with
   data in each report year; n_countries is the number of countries used.
   Limitations: The global mean is unweighted by population. The 2013 row is
   absent from the source file. Life evaluation here measures evaluative
   wellbeing and is reported separately from affect in the report.

3. ai_era_affect_indices.csv
   Description: Gallup World Poll Positive Experience Index (0 to 100),
   Negative Experience Index (0 to 100), and the share of adults worldwide who
   experienced stress during a lot of the previous day, 2015 to 2024.
   Sources: Gallup Global Emotions reports (2016 to 2024 editions) and Gallup
   State of the World's Emotional Health report (2025 edition).
   Limitations: The 2015 negative index and pre-2017 stress shares are not
   consistently published in the sources reviewed and are recorded as NA
   rather than estimated.

4. ai_era_freedom_satisfaction.csv
   Description: Satisfaction with freedom to choose what to do with one's
   life (Gallup World Poll). Contains the US series by year (2015 to 2024,
   women and, where published, all adults) and the global figures published by
   Gallup for 2017 (average), 2024 (median), and 2025 (median).
   Sources: Gallup (2018, "Freedom Rings in Places You Might Not Expect");
   Gallup (2025, "Land of the Free? Fewer Americans Agree"); Gallup (2026,
   "People Worldwide More Satisfied With Their Freedom in Life").
   Limitations: Global values before 2024 are not published as a consistent
   median series, so the chart in the report plots the available points only.
   The 2017 global figure is a worldwide average; the 2024 and 2025 figures
   are medians across countries.

5. ai_era_stress.csv
   Description: Self-reported daily stress worldwide. population_stress_pct
   is the share of all adults who experienced stress during a lot of the
   previous day (Gallup Global Emotions). workplace_stress_pct is the share of
   employees who experienced a lot of daily stress at work (Gallup State of
   the Global Workplace).
   Sources: Gallup Global Emotions reports and Gallup State of the Global
   Workplace reports (2020 to 2026 editions).
   Limitations: The two series use different samples (all adults versus
   employees) and different questions, and are plotted separately in the
   report. NA means the source did not publish a comparable value.

6. ai_era_job_security_perceived.csv
   Description: Perceived job security and attitudes toward AI at work from
   Gallup, Microsoft, and Pew surveys.
   Sources: Gallup Work and Education poll (September 2023); Microsoft Work
   Trend Index (2023 and 2024); Pew Research Center survey of US workers
   (February 2025).
   Limitations: Samples and question wording differ across surveys; the file
   records the exact question for each value so they are not conflated.

7. ai_era_ai_exposure.csv
   Description: Estimates of employment exposure to AI from the ILO (2023),
   IMF (2024), OECD (2024), and Frey and Osborne (2017).
   Sources: ILO Working Paper 96 (Generative AI and Jobs); IMF (2024, AI Will
   Transform the Global Economy); OECD (2024, generative AI and regional
   labour markets); Frey and Osborne (2017, Technological Forecasting and
   Social Change).
   Limitations: Exposure measures are not directly comparable across studies.
   The ILO clerical figure is approximate ("nearly a quarter" in the source).
   Frey and Osborne is a pre-generative-AI estimate included for historical
   context.

8. ai_era_ai_adoption_chatgpt.csv
   Description: ChatGPT user growth, 2023 to 2025.
   Sources: OpenAI announcements (2023 to 2025); UBS estimate reported by
   CNBC (2023).
   Limitations: The January 2023 figure is a third-party estimate of monthly
   active users; later figures are OpenAI's weekly active user announcements.
   The August 2025 figure was announced as "on track to reach" 700 million.

9. ai_era_ai_adoption_pew.csv
   Description: Share of US adults who have ever used ChatGPT, by year and
   age group.
   Source: Pew Research Center (June 2025; June 2026).
   Limitations: Age-group values are from the 2025 survey.

10. ai_era_ai_adoption_orgs.csv
    Description: Share of organisations using AI in at least one business
    function and the share regularly using generative AI, 2023 to 2025.
    Sources: McKinsey State of AI surveys (2023; early 2024; 2025). The
    Stanford AI Index Report (2025) re-states a later 2024 reading of
    78 percent for ai_use_pct; the primary early-2024 survey figure is 72.
    Limitations: Survey-based; samples are weighted toward larger firms.

11. ai_era_distribution.csv
    Description: Distribution of AI use and exposure across age groups,
    gender, country income groups, and urban versus rural regions.
    Sources: Pew Research Center (2025); ILO (2023 and 2026); IMF (2024);
    OECD (2024).
    Limitations: Measures differ by row (usage versus exposure) and are
    labelled accordingly.

12. ai_era_productivity_evidence.csv
    Description: Experimental evidence on generative AI and productivity,
    including effects for different skill groups.
    Sources: Noy and Zhang (2023, Science); Peng et al. (2023, arXiv);
    Brynjolfsson, Li, and Raymond (2025, Quarterly Journal of Economics);
    Cui et al. (2026, Management Science); Dell'Acqua et al. (2023, Harvard
    Business School Working Paper); Otis et al. (2024, Harvard Business School
    Working Paper, published in Management Science 2026).
    Limitations: Settings, tasks, and outcome metrics differ across studies.
    Effect sizes are within-study comparisons and are not directly
    comparable. The Otis et al. low-performer figure is approximately 10
    percent as reported in the abstract.

13. ai_era_job_transformation.csv
    Description: World Economic Forum Future of Jobs projections for job
    creation, displacement, and skill change.
    Sources: WEF Future of Jobs Report 2023 and 2025.
    Limitations: Projections based on employer surveys; they are expectations,
    not outcomes.

14. ai_era_learning_evidence.csv
    Description: Experimental evidence on generative AI and learning from
    high school mathematics (Bastani et al.).
    Source: Bastani, H., Bastani, O., Sungu, A., Ge, H., Kabakci, O., and
    Mariman, R. (2024). Generative AI Can Harm Learning. SSRN 4895486;
    published in PNAS (2025).
    Limitations: The tutor group's exam performance without access is not
    reported in the abstract and press coverage reviewed and is recorded as
    NA.

================================================================================
KEY METHODOLOGICAL CHOICES
================================================================================

The report treats the ChatGPT launch (November 2022) as the inflection point
between the pre-AI and post-AI eras. It does not attribute changes in
wellbeing or labour outcomes to AI when they could equally reflect three
confounding factors: the post-pandemic recovery, the 2022 to 2023 inflation
and cost-of-living shock, and pre-existing trends. Every section states which
indicator is used and where the evidence is thin.

Wellbeing constructs are kept separate throughout: life evaluation (Cantril
ladder), affect (Positive and Negative Experience Indexes), stress (Gallup
stress measures), and perceived freedom (Gallup freedom satisfaction). The
report does not conflate these constructs.

The non-expert empowerment question is treated as an open question. The
productivity experiments in ai_era_productivity_evidence.csv and the learning
experiment in ai_era_learning_evidence.csv are the strongest available
evidence, and the report states explicitly where results conflict (for
example, Otis et al. finding losses for low performers in a complex task).

================================================================================
REPRODUCIBILITY
================================================================================

The replication script (../scripts/replicate.py) reads these files and
reproduces every chart and every statistic quoted in the report and summary.
It requires Python 3.10 or later with matplotlib, numpy, and pandas at the
pinned versions listed at the top of the script. The World Happiness Report
file is downloaded once and cached locally.

If you use these data in your work, please cite:
Zhang, Y. (2026). Generative AI and Everyday Life: Wellbeing, Work, and Skills
Before and After ChatGPT (2015-2026). Research Brief, Auckland University of
Technology. Available at: https://zhangyuqian.com/ai-era-daily-life/
