# README_methodology.txt
# Data Methodology for Cybersecurity Risk Disclosure Research Brief
# Author: Dr Yuqian Zhang
# Date: 10 July 2026

================================================================================
1. DATA SOURCES
================================================================================

The data files in this directory were compiled from the following sources:

a) IBM Cost of a Data Breach reports (2015-2025):
   - Annual reports published by IBM Security and the Ponemon Institute
     providing global and US-specific average breach costs. Figures are
     reported in nominal USD millions.

b) Verizon Data Breach Investigations Report (DBIR) (2015-2025):
   - Annual compendium of breach incident data compiled from public and
     private sector contributors, including law enforcement agencies and
     forensic firms.

c) Privacy Rights Clearinghouse:
   - Publicly accessible database of data breach incidents in the United
     States, used to cross-validate breach frequency counts.

d) Wilson Sonsini (2025):
   - Wilson Sonsini Goodrich & Rosati (2025). The SEC's New Cybersecurity
     Rules: A Look at the First Year of 8-K Filings. Analysis covering
     December 2023 through January 2025.

e) Regulatory primary sources:
   - SEC Release 33-11216 (Final Cybersecurity Disclosure Rules, 2023).
   - EU NIS2 Directive 2022/2555.
   - EU DORA Regulation 2022/2554.
   - EU GDPR Regulation 2016/679.
   - California Consumer Privacy Act (CCPA) and CPRA amendments.

f) Ransomware data:
   - Chainalysis Crypto Crime Reports (2019-2025).
   - Coveware Quarterly Ransomware Reports (2019-2025).
   - Sophos State of Ransomware annual surveys (2019-2025).

g) Cyber insurance data:
   - Munich Re Cyber Insurance Market Outlook (2019-2025).
   - National Association of Insurance Commissioners (NAIC) Supplement on
     Cyber Insurance (2019-2025).

h) Academic literature:
   - Systematic review of cybersecurity disclosure, breach, and governance
     papers in top accounting, finance, and information systems journals.
   - Verify individual paper details (journal, volume, issue, pages, year, DOI)
     using CrossRef metadata and publisher websites.
   - Final compilation date: July 2026.

================================================================================
2. DATA FILES AND DESCRIPTIONS
================================================================================

cyber_breach_trends.csv:
  - Annual global data breach frequency and cost trends, 2015-2025.
  - Columns: year, breach_count, records_exposed_millions,
    avg_cost_per_breach_usd_millions, us_avg_cost_per_breach_usd_millions.
  - 2025 data are preliminary and subject to revision as full-year reports
    are released.

cyber_disclosure_timeline.csv:
  - Chronological record of regulatory developments and major events in
    cybersecurity disclosure, 2018-2026.
  - Columns: date, event, jurisdiction, category.
  - Events are dated to the day where available; month-level granularity
    is used where exact dates are not publicly confirmed.

cyber_incident_filings.csv:
  - Summary statistics for SEC Form 8-K Item 1.05 cybersecurity incident
    filings during the first year of the regime (Dec 2023 to Jan 2025).
  - Columns: metric, value, unit.
  - Percentages may not sum to 100 due to rounding or overlapping categories.

cyber_industry_breaches.csv:
  - Distribution of cybersecurity incident filings by industry based on
    SEC SIC codes, first year of Item 1.05 reporting.
  - Columns: industry, percent_of_filings.

cyber_ransomware_trends.csv:
  - Ransomware attack frequency, payment metrics, and organisational
    response trends, 2019-2025.
  - Columns: year, attacks_reported, ransomware_pct_of_breaches,
    total_ransom_payments_usd_millions, median_ransom_payment_usd_thousands,
    pct_organizations_hit, pct_organizations_refusing_to_pay.

cyber_insurance_market.csv:
  - Global cyber insurance market size and underwriting trends, 2019-2025.
  - Columns: year, global_premiums_usd_billions, north_america_usd_billions,
    europe_usd_billions, avg_rate_change_pct, claim_frequency_pct.

cyber_academic_literature.csv:
  - Key academic papers on cybersecurity disclosure, breaches, and
    governance published in top journals.
  - Columns: authors, year, title, journal, volume_issue, pages, doi_or_url,
    key_finding_summary.
  - Papers are selected for relevance to mandatory disclosure regimes,
    financial market consequences, and governance mechanisms.

cyber_regulatory_comparison.csv:
  - Cross-jurisdiction comparison of the SEC (US), NIS2 (EU), DORA (EU),
    and GDPR (EU) cybersecurity disclosure and notification frameworks.
  - Columns: dimension, sec_us, nis2_eu, dora_eu, gdpr_eu.
  - Compares structural features: scope, triggers, timelines, board
    oversight, penalties, third-party requirements, and national security
    carve-outs.

================================================================================
3. METHODOLOGICAL NOTES
================================================================================

- Breach cost figures are in nominal USD and are not adjusted for inflation.
  Users should apply a suitable deflator (e.g., CPI or GDP deflator) for
  real-value comparisons across time.
- Breach counts vary across sources due to differences in inclusion criteria,
  incident classification, and reporting jurisdictions. The DBIR counts
  confirmed data breaches; Privacy Rights Clearinghouse counts publicly
  reported incidents.
- Records exposed data are estimates and subject to revision when additional
  forensic information becomes available. Single events with very large
  exposure (e.g., the 2016 Yahoo breaches at approximately 3 billion records)
  can skew annual totals.
- Ransomware payment data from Chainalysis reflects payments tracked on-chain
  and may undercount payments made through untracked channels.
- The SEC incident filing data are drawn from the Wilson Sonsini (2025) study
  covering the first 14 months of Item 1.05. These early data may reflect
  transition effects as firms and their counsel adapt to the new rules.
- Industry classification follows SEC SIC codes as aggregated by Wilson
  Sonsini (2025). Trade and Services is a broad category capturing multiple
  two-digit SIC sectors.
- The academic literature list is not exhaustive. It focuses on ABS 4/4*
  and ABDC A/A* journals and emphasises papers directly relevant to
  mandatory disclosure, capital market effects, and governance.

================================================================================
4. LIMITATIONS
================================================================================

- 2025 breach and cost data are preliminary. IBM and Verizon typically
  release final annual figures in mid-2026.
- Cyber insurance market data rely on voluntary submissions to NAIC and
  Munich Re surveys; coverage may be incomplete for certain jurisdictions
  or smaller market segments.
- The SEC incident filing analysis by Wilson Sonsini (2025) captures only
  publicly filed Form 8-K disclosures. Incidents deemed immaterial and not
  publicly filed are, by definition, unobservable.
- Regulatory comparison data reflect the framework as adopted. National
  transposition of EU directives (NIS2) may vary across member states in
  practice, and guidance from supervisory authorities continues to evolve.
- Academic literature classification is based on the authors' stated
  contributions. Overlap exists between cybersecurity risk, breach
  disclosure, and IT governance research streams.

================================================================================
5. REPRODUCIBILITY
================================================================================

- Raw source data from IBM, Verizon, Chainalysis, Coveware, and Sophos
  can be obtained from the respective publishers' websites. Links are
  available on request.
- Regulatory primary sources (SEC releases, EU directives and regulations)
  are publicly available on eur-lex.europa.eu and sec.gov.
- Wilson Sonsini (2025) is a publicly available client alert and can be
  downloaded from the firm's website.
- To replicate the academic literature search: query Web of Science and
  Scopus using combinations of "cybersecurity" OR "data breach" OR "cyber
  risk" AND "disclosure" OR "reporting" OR "governance" AND "accounting"
  OR "finance", filtering by publication year through 2025 and business/
  economics subject categories.
- Individual paper DOIs can be verified at doi.org.
- The random seed for any probabilistic analyses is set to 42.
