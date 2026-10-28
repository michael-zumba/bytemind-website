-- Auckland Property Scout schema (SQLite)
-- A rebuild is atomic: db/build.py creates the database in a temp file and swaps it in.

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS suburbs (
    slug TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    tm_name TEXT,
    district TEXT,
    group_name TEXT,
    lat REAL,
    lon REAL,
    geometry_json TEXT
);

CREATE TABLE IF NOT EXISTS listings (
    id INTEGER PRIMARY KEY,
    title TEXT,
    address TEXT,
    suburb_slug TEXT NOT NULL REFERENCES suburbs(slug),
    suburb_name TEXT,
    district TEXT,
    region TEXT,
    property_type TEXT,
    bedrooms INTEGER,
    bathrooms INTEGER,
    lounges INTEGER,
    parking INTEGER,
    land_area REAL,
    floor_area REAL,
    price_display TEXT,
    asking_price INTEGER,
    asking_kind TEXT,
    sale_method TEXT,
    deadline_at TEXT,
    listed_at TEXT,
    end_at TEXT,
    as_at TEXT,
    lat REAL,
    lon REAL,
    canonical_path TEXT,
    url TEXT,
    photo_url TEXT,
    photos_json TEXT,
    body TEXT,
    agent_name TEXT,
    agency_name TEXT,
    agency_phone TEXT,
    agency_website TEXT,
    member_nickname TEXT,
    member_id INTEGER,
    view_count INTEGER,
    watchers INTEGER,
    detail_ok INTEGER NOT NULL DEFAULT 0,
    detail_error TEXT,

    -- Homes.co.nz automated valuation (primary external signal)
    estimate_low INTEGER,
    estimate_mid INTEGER,
    estimate_high INTEGER,
    estimate_source TEXT,
    estimate_updated_at TEXT,
    estimate_matched INTEGER,
    homes_property_id TEXT,
    homes_url TEXT,
    cv INTEGER,
    land_value INTEGER,
    improvement_value INTEGER,
    cv_updated_at TEXT,
    build_decade TEXT,
    build_year INTEGER,
    build_year_source TEXT,
    tenure_source TEXT,

    -- Independent comparable-sales model
    comp_low INTEGER,
    comp_mid INTEGER,
    comp_high INTEGER,
    comp_confidence TEXT,
    comp_source TEXT,
    comp_n INTEGER,
    comp_basis_json TEXT,

    -- Primary value range shown in the app
    value_low INTEGER,
    value_mid INTEGER,
    value_high INTEGER,
    value_source TEXT,
    value_confidence TEXT,
    value_basis_json TEXT,

    cv_ratio REAL,
    ask_gap REAL,
    deal_gap REAL,
    days_on_market INTEGER,
    first_seen_at TEXT,
    last_seen_at TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    delisted_at TEXT,
    is_standard INTEGER NOT NULL DEFAULT 1,
    standard_reason TEXT,
    tenure TEXT,
    sale_method_stage INTEGER,
    sale_pressure REAL,
    sale_pressure_label TEXT
);

CREATE INDEX IF NOT EXISTS idx_listings_suburb ON listings(suburb_slug);
CREATE INDEX IF NOT EXISTS idx_listings_value ON listings(value_mid);
CREATE INDEX IF NOT EXISTS idx_listings_cv ON listings(cv);
CREATE INDEX IF NOT EXISTS idx_listings_beds ON listings(bedrooms);
CREATE INDEX IF NOT EXISTS idx_listings_type ON listings(property_type);
CREATE INDEX IF NOT EXISTS idx_listings_method ON listings(sale_method);
CREATE INDEX IF NOT EXISTS idx_listings_geo ON listings(lat, lon);
CREATE INDEX IF NOT EXISTS idx_listings_listed ON listings(listed_at);
CREATE INDEX IF NOT EXISTS idx_listings_dom ON listings(days_on_market);
CREATE INDEX IF NOT EXISTS idx_listings_status ON listings(status);
CREATE INDEX IF NOT EXISTS idx_listings_delisted ON listings(delisted_at);

CREATE TABLE IF NOT EXISTS listing_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    captured_at TEXT NOT NULL,
    price_display TEXT,
    asking_price INTEGER,
    estimate_mid INTEGER,
    cv INTEGER,
    view_count INTEGER,
    watchers INTEGER,
    days_on_market INTEGER,
    value_mid INTEGER,
    sale_method TEXT,
    UNIQUE(listing_id, captured_at)
);

CREATE TABLE IF NOT EXISTS estimate_history (
    listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    date TEXT NOT NULL,
    estimate_low INTEGER,
    estimate_mid INTEGER,
    estimate_high INTEGER,
    PRIMARY KEY (listing_id, date)
);

CREATE TABLE IF NOT EXISTS suburb_estimate_history (
    suburb_slug TEXT NOT NULL REFERENCES suburbs(slug),
    date TEXT NOT NULL,
    estimate_mid INTEGER,
    PRIMARY KEY (suburb_slug, date)
);

CREATE TABLE IF NOT EXISTS properties (
    id TEXT PRIMARY KEY,
    homes_property_id TEXT,
    address TEXT,
    suburb TEXT,
    lat REAL,
    lon REAL,
    cv INTEGER,
    land_value INTEGER,
    improvement_value INTEGER,
    land_area REAL,
    floor_area REAL,
    bedrooms INTEGER,
    bathrooms INTEGER,
    property_type TEXT,
    build_decade TEXT,
    cv_updated_at TEXT,
    last_sale_price INTEGER,
    last_sale_date TEXT
);

CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id TEXT,
    address TEXT,
    suburb TEXT,
    sale_price INTEGER NOT NULL,
    sale_date TEXT,
    lat REAL,
    lon REAL,
    land_area REAL,
    floor_area REAL,
    bedrooms INTEGER,
    bathrooms INTEGER,
    property_type TEXT,
    cv INTEGER,
    land_value INTEGER,
    improvement_value INTEGER,
    estimate_low INTEGER,
    estimate_mid INTEGER,
    estimate_high INTEGER,
    distance_km REAL,
    source TEXT,
    source_detail TEXT,
    UNIQUE(property_id, sale_date, sale_price)
);

CREATE INDEX IF NOT EXISTS idx_sales_geo ON sales(lat, lon);
CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date);
CREATE INDEX IF NOT EXISTS idx_sales_property ON sales(property_id);

CREATE TABLE IF NOT EXISTS schools (
    id INTEGER PRIMARY KEY,
    name TEXT,
    type TEXT,
    authority TEXT,
    roll INTEGER,
    gender TEXT,
    decile INTEGER,
    address TEXT,
    suburb TEXT,
    lat REAL,
    lon REAL
);

CREATE TABLE IF NOT EXISTS listing_schools (
    listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    school_id INTEGER NOT NULL REFERENCES schools(id),
    in_zone INTEGER,
    PRIMARY KEY (listing_id, school_id)
);

CREATE TABLE IF NOT EXISTS listing_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    event_at TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    detail_json TEXT,
    UNIQUE(listing_id, event_type, event_at, old_value, new_value)
);

CREATE INDEX IF NOT EXISTS idx_events_listing ON listing_events(listing_id, event_at);

-- Dated price observations and changes. One row per distinct observed state,
-- not one row per daily scrape: the event ledger already preserves every
-- observed change. "price" is the asking price; NULL means auction/POA/no price.
CREATE TABLE IF NOT EXISTS listing_price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    observed_at TEXT NOT NULL,
    price INTEGER,
    price_display TEXT,
    sale_method TEXT,
    event_type TEXT NOT NULL,
    previous_price INTEGER,
    change_amount INTEGER,
    change_pct REAL,
    days_since_previous REAL,
    source TEXT
);
CREATE INDEX IF NOT EXISTS idx_price_history_listing
    ON listing_price_history(listing_id, observed_at);
CREATE INDEX IF NOT EXISTS idx_price_history_event
    ON listing_price_history(event_type, observed_at);

-- Per-listing speed/sentiment indicators derived from listing_price_history.
CREATE TABLE IF NOT EXISTS listing_price_dynamics (
    listing_id INTEGER PRIMARY KEY REFERENCES listings(id) ON DELETE CASCADE,
    first_price INTEGER,
    current_price INTEGER,
    n_observations INTEGER NOT NULL DEFAULT 0,
    n_price_changes INTEGER NOT NULL DEFAULT 0,
    n_description_changes INTEGER NOT NULL DEFAULT 0,
    first_change_at TEXT,
    last_change_at TEXT,
    first_description_change_at TEXT,
    last_description_change_at TEXT,
    days_to_first_change REAL,
    days_since_last_change REAL,
    avg_days_between_changes REAL,
    cumulative_change INTEGER,
    cumulative_change_pct REAL,
    largest_drop INTEGER,
    largest_drop_pct REAL,
    last_direction TEXT,
    updated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_price_dynamics_change
    ON listing_price_dynamics(n_price_changes, last_change_at);

-- Property-level sale history from Homes.co.nz (subject property, not nearby comps).
CREATE TABLE IF NOT EXISTS property_sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    homes_property_id TEXT NOT NULL,
    listing_id INTEGER REFERENCES listings(id) ON DELETE SET NULL,
    address TEXT,
    sale_date TEXT,
    sale_price INTEGER,
    display_price TEXT,
    sale_type TEXT,
    council_confirmed INTEGER,
    source TEXT,
    updated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_property_sales_property
    ON property_sales(homes_property_id, sale_date);
CREATE INDEX IF NOT EXISTS idx_property_sales_listing
    ON property_sales(listing_id, sale_date);

-- Realised sale outcomes matched to the prior listing campaign. A row exists only
-- when the same Homes property has a disclosed sale on/after the listing start.
CREATE TABLE IF NOT EXISTS listing_sale_outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    homes_property_id TEXT NOT NULL,
    sale_date TEXT NOT NULL,
    sale_price INTEGER NOT NULL,
    sale_display TEXT,
    listing_listed_at TEXT,
    listing_first_seen_at TEXT,
    asking_price INTEGER,
    estimate_low INTEGER,
    estimate_mid INTEGER,
    estimate_high INTEGER,
    value_low INTEGER,
    value_mid INTEGER,
    value_high INTEGER,
    comp_mid INTEGER,
    cv INTEGER,
    suburb_slug TEXT,
    suburb_name TEXT,
    property_type TEXT,
    bedrooms INTEGER,
    bathrooms INTEGER,
    land_area REAL,
    floor_area REAL,
    build_year INTEGER,
    build_decade TEXT,
    tenure TEXT,
    sale_method TEXT,
    days_listing_to_sale REAL,
    prediction_error INTEGER,
    prediction_abs_error INTEGER,
    prediction_abs_pct REAL,
    within_80_interval INTEGER,
    prediction_source TEXT,
    source TEXT,
    matched_at TEXT,
    UNIQUE(listing_id, homes_property_id, sale_date, sale_price)
);
CREATE INDEX IF NOT EXISTS idx_sale_outcomes_listing
    ON listing_sale_outcomes(listing_id, sale_date);
CREATE INDEX IF NOT EXISTS idx_sale_outcomes_suburb
    ON listing_sale_outcomes(suburb_slug, sale_date);

-- Rolling calibration of the prior value signal against realised sale prices.
CREATE TABLE IF NOT EXISTS sale_feedback_calibration (
    scope TEXT NOT NULL,
    scope_key TEXT NOT NULL,
    n INTEGER NOT NULL,
    median_ratio REAL,
    mean_ratio REAL,
    median_abs_pct REAL,
    mae REAL,
    coverage_80 REAL,
    updated_at TEXT,
    PRIMARY KEY (scope, scope_key)
);

CREATE TABLE IF NOT EXISTS model_predictions (
    listing_id INTEGER NOT NULL,
    model_name TEXT NOT NULL,
    low INTEGER,
    mid INTEGER,
    high INTEGER,
    confidence TEXT,
    basis_json TEXT,
    created_at TEXT,
    PRIMARY KEY(listing_id, model_name)
);

CREATE TABLE IF NOT EXISTS model_metrics (
    model_name TEXT NOT NULL,
    metric TEXT NOT NULL,
    value REAL,
    detail_json TEXT,
    created_at TEXT,
    PRIMARY KEY(model_name, metric)
);

CREATE TABLE IF NOT EXISTS sale_method_analysis (
    stage INTEGER PRIMARY KEY,
    label TEXT,
    n INTEGER,
    median_value_ratio REAL,
    median_ask_gap REAL,
    median_dom REAL,
    median_avm_cv REAL,
    ols_coef REAL,
    ols_p REAL,
    ols_n INTEGER,
    ols_r2 REAL,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS suburb_stats (
    suburb_slug TEXT PRIMARY KEY REFERENCES suburbs(slug),
    active_count INTEGER,
    median_value INTEGER,
    median_asking INTEGER,
    median_cv INTEGER,
    median_land REAL,
    median_floor REAL,
    median_dom REAL,
    min_value INTEGER,
    max_value INTEGER,
    avm_cv_ratio REAL,
    median_sold INTEGER,
    median_sold_cv_ratio REAL,
    sold_count INTEGER,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS scrape_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT,
    finished_at TEXT,
    status TEXT,
    suburb_count INTEGER,
    listing_count INTEGER,
    detail_ok INTEGER,
    missing_estimate INTEGER,
    notes TEXT
);

-- Convenience views ---------------------------------------------------------
DROP VIEW IF EXISTS v_listing_cards;
CREATE VIEW v_listing_cards AS
SELECT
    l.*,
    l.suburb_name AS suburb,
    s.name AS suburb_display,
    s.group_name AS suburb_group
FROM listings l
JOIN suburbs s ON s.slug = l.suburb_slug;
