# README_methodology.txt
# Data Methodology for Blockchain and Cryptocurrency Research Brief
# Author: Dr Yuqian Zhang
# Date: 10 July 2026

================================================================================
1. DATA SOURCES
================================================================================

The data files in this directory were compiled from the following sources:

a) Public market and on-chain data:
   - CoinGecko (coingecko.com) and CoinMarketCap (coinmarketcap.com) for
     total cryptocurrency market capitalisation, Bitcoin price, and
     dominance data. CoinGecko launched in 2014; data prior to 2014
     should be treated as estimates with wider margins of uncertainty.
   - DeFiLlama (defillama.com) for DeFi total value locked (TVL) and
     stablecoin market capitalisation data.
   - Farside Investors (farside.co.uk) for spot Bitcoin and Ether ETF
     flow data, updated daily. Data retrieved 9 July 2026.
   - NonFungible (nonfungible.com), Demandsage, CoinLedger for NFT
     market volume estimates.

b) Corporate treasury data:
   - SEC EDGAR (sec.gov) for corporate 8-K and 10-K filings of publicly
     listed companies with crypto holdings.
   - Strategy (MicroStrategy) official 8-K filings at strategy.com/purchases
     for verified Bitcoin treasury data.
   - bitcointreasuries.net and bitbo.io/treasuries for aggregate tracking.

c) Regulatory and standard-setting publications:
   - EU MiCA Regulation (EU) 2023/1114 and related ESMA publications.
   - SEC orders and releases at sec.gov.
   - FASB ASU 2023-08, official pronouncement at fasb.org.
   - FATF guidance documents at fatf-gafi.org.
   - Atlantic Council CBDC Tracker (atlanticcouncil.org/cbdctracker).
   - BIS CBDC surveys (2021, 2022, 2023).

d) Exchange failure data:
   - Court filings (FTX, Celsius, Voyager, BlockFi, Genesis, 3AC).
   - Chainalysis Crypto Crime Reports for loss estimates.
   - Investopedia, TheStreet for event chronologies; cross-validated.

e) Academic literature:
   - Systematic review of blockchain and cryptocurrency papers in top
     finance (JF, JFE, RFS), management (MS), and accounting (JAR, JAE,
     TAR, CAR, RAST) journals.
   - Verification of bibliographic details (DOI, volume, issue, pages) via
     CrossRef metadata and publisher websites.

================================================================================
2. DATA FILES AND DESCRIPTIONS
================================================================================

crypto_market_cap.csv: Year-end total cryptocurrency market capitalisation,
  Bitcoin price, and Bitcoin dominance percentage, 2013-2025.

crypto_corporate_treasury.csv: Publicly listed firms holding Bitcoin on
  their balance sheets, mid-2026.

crypto_regulatory_timeline.csv: Key regulatory events globally, 2013-2026.

crypto_exchange_failures.csv: Major exchange and protocol failures, 2014-2022.

crypto_etf_flows.csv: Cumulative net flows for US spot Bitcoin ETFs as of
  9 July 2026.

crypto_cbdc_progress.csv: Number of countries exploring, piloting, and
  launching CBDCs by year.

crypto_academic_literature.csv: Key academic papers on blockchain and
  cryptocurrency published in ABS 4/4* and ABDC A/A* journals.

crypto_defi_stablecoin_nft.csv: DeFi TVL, stablecoin market cap, and NFT
  annual sales volume, 2017-2025.

================================================================================
3. METHODOLOGICAL NOTES
================================================================================

- All dollar figures are nominal USD and not adjusted for inflation.
- Market cap figures prior to 2017 have limited altcoin coverage.
- DeFi TVL data are from DeFiLlama. Pre-2020 data are approximate.
- The FTX loss estimate ($9B) covers customer funds.
- The Terra/LUNA loss estimate ($55B) reflects market capitalisation destruction.
- Strategy Bitcoin holdings data are verified against primary SEC 8-K filings.
- Academic literature is limited to top finance, management, and accounting journals.
- The random seed for any probabilistic analyses is set to 42.

================================================================================
4. LIMITATIONS
================================================================================

- On-chain data quality varies by source. CoinGecko and CoinMarketCap
  both exclude wash trading to the extent detectable.
- Corporate treasury data rely on voluntary disclosure of crypto holdings.
- Regulatory timeline focuses on major jurisdictions (US, EU, China, Japan, UK, AU).
- NFT volume data are particularly unreliable prior to 2020.
- Exchange failure loss estimates vary across sources and are subject to
  ongoing litigation and recovery.

================================================================================
5. REPRODUCIBILITY
================================================================================

- CoinGecko and CoinMarketCap historical data via public APIs or web snapshots.
- DeFiLlama TVL data can be replicated via defillama.com API.
- SEC filings are publicly available via EDGAR (sec.gov).
- Strategy 8-K filings are linked at strategy.com/purchases.
- Farside Investors data at farside.co.uk/btc and farside.co.uk/eth.
- Atlantic Council CBDC Tracker at atlanticcouncil.org/cbdctracker.
- Academic paper DOIs can be verified at doi.org.
