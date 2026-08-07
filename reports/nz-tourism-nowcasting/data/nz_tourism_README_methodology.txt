================================================================================
METHODOLOGY DOCUMENTATION
Big Data and AI in Business Operations: Google Trends Nowcasting of
New Zealand Tourism Demand and AI Adoption in the Sector
Dr Yuqian Zhang, 10 July 2026
================================================================================

1. DATA SOURCES
================================================================================

1.1 NZ Monthly Overseas Visitor Arrivals
    Source:      Stats NZ, International Travel (April 2026 release)
    URL:         https://www.stats.govt.nz/information-releases/international-travel-april-2026/
    Coverage:    April 2016 to April 2026 (121 months)
    Frequency:   Monthly
    Variable:    Actual (unadjusted) overseas visitor arrivals
    Revision:    Stats NZ may revise historical figures; figures used here
                 are as published in the April 2026 release. The January 2023
                 figure was revised in the April 2026 release to correct a
                 cruise ship passenger list error.
    Methodology: Arrivals counted from arrival cards (pre-November 2018) and
                 Customs passport data matched with arrival cards (post-
                 November 2018). Country of residence imputation applied
                 August 2016 to October 2018.

1.2 Google Trends Search Indices
    Source:      Google Trends (trends.google.com)
    Queries:     "new zealand travel", "new zealand tourism",
                 "new zealand holiday"
    Geography:   New Zealand (country level)
    Date range:  1 January 2010 to 30 June 2026
    Retrieved:   10 July 2026
    Frequency:   Monthly
    Scale:       0 to 100, relative to peak search share within the query
                 window. A value of 50 means half the peak search share.
    Limitations: Google Trends uses a sample (not the full search universe).
                 Repeated pulls of the same query will vary slightly.
                 Adding or removing date ranges can rescale the entire series.
                 Low-volume queries may be suppressed (reported as zero)
                 due to privacy thresholds. The series measures searches
                 within the NZ geography, not searches by overseas visitors.
                 Source-market geographies would likely yield stronger
                 correlations for the tourism application; the NZ geography
                 was chosen as a transparent, reproducible baseline.

1.3 Tourism Satellite Account (Economic Contribution)
    Source:      Stats NZ, Tourism Satellite Account (year ended March 2025)
    URL:         https://www.stats.govt.nz/information-releases/tourism-satellite-account-year-ended-march-2025/
    Coverage:    Annual (year ended March), latest: March 2025
    Variables:   Total tourism expenditure, international expenditure,
                 domestic expenditure, direct and total GDP contribution,
                 direct and total employment.

1.4 NZ AI Adoption Statistics
    Sources:
      - AI Forum New Zealand / Kinetics (2025). State of AI in New Zealand.
      - MBIE (2025). New Zealand's Strategy for Artificial Intelligence.
      - NZIER / Spark (2024). AI Activity in New Zealand: SME Adoption.
      - Datacom survey data cited in MBIE (2025).
      Note: These are survey-based estimates. Definitions of AI vary across
      surveys, and figures should not be directly compared between surveys
      without noting definitional differences.

1.5 AI Tourism Case Studies
    Sources: Reseller News NZ (Air NZ), ChannelLife/NZ Herald (Sudima Hotels),
             Tourism NZ/GuideGeek press releases, NIWA, industry reports.
    All case study claims verified against primary sources as of 10 July 2026.
    Where primary reports used ranges (e.g., Sudima "10-15%"), these are
    reported as ranges rather than point estimates.

1.6 Academic Literature
    Sources: Publisher databases (Wiley, Elsevier, Taylor & Francis, Springer),
             Google Scholar, journal websites.
    Verification: DOIs verified by attempting resolution; journal rankings
                 from ABS 2021 and ABDC 2022 lists.
    Date of verification: 10 July 2026.

================================================================================
2. FILE DESCRIPTIONS
================================================================================

2.1 nz_tourism_arrivals_google_trends.csv
    Monthly panel (121 rows) combining Stats NZ overseas visitor arrivals
    with Google Trends search indices.
    Columns:
      month             YYYY-MM format
      visitor_arrivals  Actual monthly overseas visitor arrivals (integer)
      gt_travel         Google Trends "new zealand travel" index (0-100)
      gt_tourism        Google Trends "new zealand tourism" index (0-100)
      gt_holiday        Google Trends "new zealand holiday" index (0-100)
      gt_composite      Simple average of the three indices

2.2 nz_tourism_arrivals_annual.csv
    Calendar-year totals of overseas visitor arrivals (2017 to 2026 partial).
    Columns:
      year            Calendar year
      visitor_arrivals Total arrivals (integer; 2026 is Jan-Apr partial)
      peak_month      Month with highest arrivals in that year
      peak_arrivals   Arrivals in the peak month
      notes           Context (e.g., COVID border closure, travel bubble)

2.3 nz_tourism_economic_contribution.csv
    Key economic metrics from the Tourism Satellite Account and MBIE.
    Columns:
      metric    Description of the indicator
      value     Numeric value
      unit      Unit of measurement
      period    Time period the value refers to
      source    Primary source

2.4 nz_tourism_ai_adoption.csv
    AI adoption indicators for NZ business overall and the tourism sector.
    Columns:
      indicator  Description of the indicator
      value      Numeric or approximate value
      unit       Unit (%, users, NZD, etc.)
      year       Reference year
      source     Primary source

2.5 nz_tourism_academic_literature.csv
    Peer-reviewed papers on Google Trends nowcasting and tourism demand
    forecasting.
    Columns:
      authors       Author names
      year          Publication year
      title         Paper title
      journal       Journal name
      volume        Volume and issue
      pages         Page range
      doi           Digital Object Identifier
      abs_ranking   ABS Academic Journal Guide 2021 rating
      abdc_ranking  ABDC Journal Quality List 2022 rating
      topic         Brief topic descriptor

2.6 nz_tourism_README_methodology.txt
    This file.

================================================================================
3. ANALYSIS NOTES
================================================================================

3.1 Correlation Analysis
    Pearson correlation coefficients computed between monthly visitor
    arrivals and Google Trends indices. Full sample (April 2016 to
    April 2026, n=121) and four sub-periods:
      Pre-COVID:     April 2016 to February 2020 (n=47)
      During COVID:  March 2020 to February 2022 (n=24)
      Recovery:      March 2022 to April 2026 (n=50)
      Post-recovery: April 2023 to April 2026 (n=37)

    The full-sample correlation of r=0.71 between the "new zealand holiday"
    index and arrivals is mechanically inflated by the pandemic, because both
    search interest and arrivals fell near zero together and recovered
    together. The pre-COVID and post-recovery sub-period correlations are
    more informative about the relationship in normal operating conditions.

3.2 Composite Index
    The composite index is a simple arithmetic mean:
      composite = (gt_travel + gt_tourism + gt_holiday) / 3
    More sophisticated composites (PCA-weighted, MIDAS-weighted) would likely
    improve performance and should be explored in follow-up research.

3.3 Charts
    All charts in the HTML research brief were generated with ECharts 5.5.0
    using the data from these CSV files. Chart data values are embedded in
    the HTML and can be cross-referenced against the CSV files.

3.4 Reproducibility
    To reproduce the Google Trends data, visit:
    https://trends.google.com/trends/explore?date=2010-01-01%202026-06-30&geo=NZ
    and enter the three queries listed in section 1.2. Note that Google
    Trends indices are sampled, so values will differ slightly on each pull,
    but the patterns and correlations should be stable.

    To reproduce the arrivals data, download the latest International Travel
    release from Stats NZ or use Infoshare (Tourism > International Travel
    and Migration - ITM).

    The Python script that generated the CSV files is available alongside
    this dataset.

================================================================================
4. LIMITATIONS
================================================================================

- Google Trends indices are relative and sampled. Small variations between
  pulls are expected and do not affect the substantive findings.
- The NZ geography for Google Trends measures searches within New Zealand,
  not searches by prospective international visitors. Source-market
  geographies would be preferable for tourism forecasting and should be
  explored in follow-up research.
- Correlations are not causal. Search interest may be driven by factors
  other than travel intent (e.g., general news or curiosity).
- AI adoption survey data rely on self-reporting and varying definitions
  of "AI" across surveys. Figures from different sources should not be
  directly compared.
- Case study data come from company disclosures and media reports, not
  independently audited sources.
- The COVID-19 pandemic creates a structural break in the search-arrivals
  relationship. Models fitted on pre-COVID data may not transfer to
  post-COVID conditions without adjustment.
- RECOVERY CHART NOTE: The January 2023 recovery percentage in Figure 5
  uses 67.2% from the Stats NZ published "proportion of 2019" table. The
  computed value from the revised January 2023 arrival figure (266,432)
  would be 66.7%. Stats NZ revised the January 2023 arrival data in the
  April 2026 release to correct a cruise ship passenger list error, but
  the published percentage-of-2019 table was not updated after the revision.
  We use the official published table figure (67.2%) to remain consistent
  with the source document. Both values round to 67% when reported to the
  nearest whole percent.

================================================================================
5. CITATION
================================================================================

If you use these data in academic work, please cite the accompanying
research brief:

  Zhang, Y. (2026). Big Data and AI in Business Operations: Google Trends
  Nowcasting of New Zealand Tourism Demand and AI Adoption in the Sector.
  Research Brief, 10 July 2026.

================================================================================
Dr Yuqian Zhang | 10 July 2026
================================================================================
