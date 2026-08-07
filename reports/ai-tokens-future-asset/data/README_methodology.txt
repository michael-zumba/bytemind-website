AI Tokens as an Emerging Asset Class: Data and Methodology
Dr Yuqian Zhang, Auckland University of Technology
Date: 23 July 2026

================================================================================
OVERVIEW
================================================================================

This directory contains the datasets used in the research brief "AI Tokens
as an Emerging Asset Class: Economic Logic, Market Evidence, and Accounting
Implications." Each dataset is described below with its source, compilation
method, and known limitations.

================================================================================
DATASET DESCRIPTIONS
================================================================================

1. ai_tokens_market_cap.csv
   Description: Quarterly AI token sector market capitalisation and dominance
   relative to total crypto market (2020 Q1 to 2026 Q2).
   Sources: Compiled from CoinGecko, CoinMarketCap AI & Big Data category
   aggregates, and individual token data. Early-period estimates (2020-2021)
   are approximate due to limited AI token categorisation at the time.
   Key columns: year, quarter, total_market_cap_usd_billion,
   btc_market_cap_usd_billion, ai_token_count, ai_token_dominance_pct
   Limitations: Market cap data are end-of-quarter snapshots and do not
   capture intra-quarter volatility. AI token category definitions vary
   across data platforms. Tokens listed as AI-related include some
   borderline cases (e.g., data storage tokens used by AI projects).

2. ai_tokens_top_projects.csv
   Description: Major AI-focused blockchain projects by market capitalisation
   as of Q2 2026.
   Sources: CoinMarketCap AI & Big Data category (July 2026 snapshot),
   individual project documentation, CoinGecko.
   Key columns: token, ticker, category, launch_date,
   market_cap_usd_billion_q2_2026, ath_price_usd, ath_date, use_case, blockchain
   Limitations: ATH figures from CoinMarketCap may differ from exchange-
   specific data due to price aggregation methodology. Market cap rankings
   are point-in-time and shift rapidly in this sector.

3. ai_tokens_price_history.csv
   Description: End-of-quarter price and market cap for five major AI tokens
   (TAO, RNDR, FET, AKT, NEAR) from Q1 2023 to Q2 2026.
   Sources: CoinMarketCap and CoinGecko historical data endpoints.
   Key columns: token_ticker, token_name, year, month, price_usd,
   market_cap_usd_million
   Limitations: Prices are approximate quarter-end values. FET data before
   the ASI merger (July 2024) refers to the original FET token; post-merger
   reflects the Artificial Superintelligence Alliance token.

4. ai_tokens_corporate_adoption.csv
   Description: Corporate holdings, treasury strategies, and institutional
   investment vehicles related to AI tokens and digital assets.
   Sources: SEC EDGAR filings, corporate press releases, Bitcoin Treasuries
   (bitcointreasuries.net), Grayscale product pages.
   Key columns: company, type, holding, estimated_value_usd_million, date, notes
   Limitations: Corporate AI token holdings are difficult to verify
   comprehensively. Most publicly listed firms do not break out AI tokens
   separately from general crypto holdings. Grayscale fund AUM is not
   publicly disclosed in real time.

5. ai_tokens_vc_funding.csv
   Description: Quarterly venture capital funding in the AI-crypto sector.
   Sources: Compiled from PitchBook, Crunchbase, Messari, and project press
   releases. Aggregate figures are estimates based on available deal data.
   Key columns: year, quarter, vc_funding_usd_billion, number_of_deals,
   notable_deals
   Limitations: Many crypto VC deals are undisclosed or announced without
   funding amounts. Data likely undercounts seed-stage and private
   investments. Figures are estimated aggregates and may differ from
   proprietary databases.

6. ai_tokens_accounting_comparison.csv
   Description: Comparison of accounting frameworks applicable to AI tokens
   under US GAAP and IFRS.
   Sources: FASB ASU 2023-08, IAS 38, IAS 2, IFRS IC Agenda Decision (June
   2019), SEC SAB 121, EU MiCA.
   Key columns: standard, framework, classification, measurement,
   effective_date, key_features
   Limitations: The IASB has not issued a dedicated crypto-asset standard.
   IFRS classification depends on facts and circumstances of each holder.
   This table represents a general framework and may not apply to all
   specific arrangements.

7. ai_tokens_regulatory_timeline.csv
   Description: Chronology of major regulatory and standard-setting
   developments affecting AI tokens and crypto assets.
   Sources: SEC, FASB, IASB, European Commission, BIS, official press
   releases and publications.
   Key columns: date, event, jurisdiction, category, significance
   Limitations: Focuses on major jurisdictions (US, EU). Does not include
   all national-level regulatory actions. Timelines for proposed rules may
   shift.

8. ai_tokens_academic_literature.csv
   Description: Selected academic articles from ABS 4/4* and ABDC-A*
   journals relevant to AI tokens, crypto assets, and tokenisation.
   Sources: Scopus, Web of Science, SSRN, journal websites.
   Key columns: journal, title, authors, volume, pages, year, topic,
   evidence_type, key_findings
   Limitations: Not a systematic review. Selection emphasises top-tier
   accounting and finance journals. Literature on AI tokens specifically
   is nascent; many entries are on broader crypto/blockchain topics.

================================================================================
DATA QUALITY AND REPRODUCIBILITY
================================================================================

All datasets were compiled manually from public sources and cross-checked
where possible. Data were verified against at least two independent sources
for major figures (market capitalisation, regulatory dates, corporate
holdings). Remaining discrepancies are noted in the limitations for each
dataset.

The Python replication script (scripts/replicate.py) loads these datasets
and reproduces all charts and statistics in the report. For data obtained
from public, open-access sources, the script auto-downloads fresh data where
available. For manually compiled data, the script reads directly from CSV
files.

Last updated: 23 July 2026
