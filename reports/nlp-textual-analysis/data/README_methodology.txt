# README_methodology.txt
# Data Methodology for NLP/Textual Analysis in Accounting and Finance Research Brief
# Author: Dr Yuqian Zhang
# Date: 10 July 2026

================================================================================
1. DATA SOURCES
================================================================================

The data files in this directory were compiled from the following sources:

a) Academic literature survey:
   - Bochkay, K., Brown, S.V., Leone, A.J., and Tucker, J.W. (2023). "Textual
     Analysis in Accounting: What's Next?" Contemporary Accounting Research,
     40(2), 765-805. This survey provides a systematic count of textual analysis
     publications in top journals, which forms the baseline for publication
     trend estimates.

b) Web of Science (WoS) topic search:
   - Search terms: "textual analysis" OR "natural language processing" OR
     "text mining" OR "computational linguistics" combined with "account*" OR
     "financ*" filtered for Business and Economics categories, 2005-2025.
   - Used to cross-validate and supplement the Bochkay et al. (2023) counts
     for 2023-2025.

c) Google Scholar citation counts:
   - Citation counts for top papers were retrieved in July 2026 and represent
     cumulative citations as of that date. Minor fluctuations occur with
     subsequent indexing updates.

d) Manual verification:
   - Individual paper details (journal, volume, issue, pages, year, DOI) were
     verified against publisher websites and CrossRef metadata.

================================================================================
2. DATA FILES AND DESCRIPTIONS
================================================================================

nlp_publication_trends.csv:
  - Annual counts of textual analysis/NLP papers in top accounting and finance
    journals from 2005 to 2025.
  - Columns: year, total (all journals), journal_top5 (JAR, JAE, TAR, CAR, RAST),
    journal_top4 (JF, JFE, RFS, MS), phase (historical period).
  - 2025 data are partial (through June 2026).

nlp_method_evolution.csv:
  - Approximate percentage distribution of NLP methods used across six periods
    from 2005 to 2025.
  - Methods: dictionary/bag-of-words, readability, topic modeling, word
    embeddings, traditional ML, transformers/BERT, large language models.

nlp_journal_distribution.csv:
  - Distribution of textual analysis papers across 11 journal categories
    (cumulative through 2025).
  - Includes journal name, abbreviation, paper count, and percentage.

nlp_citation_analysis.csv:
  - Top 16 most-cited papers with verified bibliographic details.
  - Citation counts from Google Scholar, retrieved July 2026.

nlp_application_area_trends.csv:
  - Distribution of research applications across seven thematic areas over
    six time periods.

nlp_data_source_trends.csv:
  - Usage counts of eight major textual data sources across six time periods.

================================================================================
3. METHODOLOGICAL NOTES
================================================================================

- Publication counts are cumulative within each year and represent unique
  papers (not weighted by citations or journal prestige).
- "Top 5" accounting journals: Journal of Accounting Research (JAR), Journal
  of Accounting and Economics (JAE), The Accounting Review (TAR), Contemporary
  Accounting Research (CAR), Review of Accounting Studies (RAST).
- "Top 4" finance journals: Journal of Finance (JF), Journal of Financial
  Economics (JFE), Review of Financial Studies (RFS), Management Science (MS).
  Note: MS is a general management journal but publishes substantial finance
  and accounting research.
- Method classification is based on the primary NLP technique employed. Papers
  using multiple methods are classified by their most advanced method.
- Data source counts are not mutually exclusive; a paper may use multiple
  textual sources.
- Citation counts reflect Google Scholar's broad indexing and may differ from
  WoS or Scopus counts, which are typically lower.

================================================================================
4. LIMITATIONS
================================================================================

- Publication counts for 2024-2025 may be undercounted due to indexing delays.
- The "Other" category in journal distribution includes journals such as
  Journal of Accounting and Public Policy, Journal of Business Finance and
  Accounting, and other ABS 4-rated journals.
- Method classification involves judgment calls, particularly for papers
  combining multiple NLP techniques.
- Data source categorisation is approximate; some papers use proprietary
  datasets not easily classified into standard categories.

================================================================================
5. REPRODUCIBILITY
================================================================================

- Raw search data and processing scripts are available on request.
- To replicate the WoS search: use the Advanced Search with the query string
  documented in Section 1(b), filter by publication years 2005-2025, and
  export in tab-delimited format.
- Google Scholar citation counts can be verified by searching each DOI.
- The random seed for any probabilistic analyses is set to 42.
