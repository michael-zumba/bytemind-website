# README_methodology.txt
# Data Methodology for AI and Digital Transformation Research Brief
# Author: Dr Yuqian Zhang
# Date: 10 July 2026

================================================================================
1. DATA SOURCES
================================================================================

The data files in this directory were compiled from the following sources:

a) OECD ICT Access and Usage by Businesses Database (2021-2025), for AI
   adoption rates by sector, firm size, and over time.

b) McKinsey Global Survey on AI (2020-2025), for broader enterprise adoption
   and generative AI use estimates.

c) Industry surveys and disclosures from PwC, Deloitte, EY, KPMG, and the
   Conference Board/ESGAUGE, for firm performance, Big Four investment, and
   S&P 500 AI risk disclosure trends.

d) IMD World Digital Competitiveness Ranking (2024), European Commission
   DESI (2024), and World Bank Digital Adoption Index (2016), for country
   digital readiness.

e) Peer-reviewed literature and regulatory publications, including the EU AI
   Act and SEC disclosure discussions, for the research gaps and regulatory
   timeline.

================================================================================
2. DATA FILES AND DESCRIPTIONS
================================================================================

ai_adoption_by_sector.csv:
  - AI adoption rates by economic sector, OECD (2021-2025).

ai_adoption_by_firm_size.csv:
  - AI adoption rates by firm size category, OECD (2020-2024).

ai_adoption_timeline.csv:
  - Aggregate AI and generative AI adoption timeline, OECD and McKinsey.

ai_productivity_effects.csv:
  - Firm-level and macroeconomic AI productivity estimates.

ai_investment_disclosures.csv:
  - Corporate AI investment, disclosure, and litigation trends.

country_digital_readiness.csv:
  - Multi-index country digital readiness scores (IMD, DESI, DAI).

academic_literature_summary.csv:
  - Key academic literature on AI, digital transformation, and accounting.

regulatory_timeline.csv:
  - Chronology of AI and digital reporting regulatory developments.

All figures were independently reproduced from these files; see scripts/replicate.py.
