# Data Dictionary

Column-level reference for source datasets and analytical marts. Updated as data is profiled and loaded.

---

## Source: Avazu Mobile Ad Click Data

**File:** `data/raw/avazu_train.csv`  
**Status:** Pending acquisition

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer | Unique impression identifier |
| `click` | integer (0/1) | Whether the ad was clicked |
| `hour` | string | Timestamp encoded as YYYYMMDDHH |
| `C1` | categorical | Anonymous feature |
| `banner_pos` | integer | Banner position |
| `site_id` | categorical | Publisher site identifier |
| `site_domain` | categorical | Publisher domain |
| `site_category` | categorical | Site category |
| `app_id` | categorical | Application identifier |
| `app_domain` | categorical | Application domain |
| `app_category` | categorical | Application category |
| `device_id` | categorical | Device identifier |
| `device_ip` | categorical | Device IP (hashed) |
| `device_model` | categorical | Device model |
| `device_type` | integer | Device type code |
| `device_conn_type` | integer | Connection type code |
| `C14` | numeric | Anonymous feature |
| `C15` | numeric | Anonymous feature |
| `C16` | numeric | Anonymous feature |
| `C17` | numeric | Anonymous feature |
| `C18` | numeric | Anonymous feature |
| `C19` | numeric | Anonymous feature |
| `C20` | numeric | Anonymous feature |
| `C21` | numeric | Anonymous feature |

### Derived Fields (after cleaning)

| Column | Type | Description |
|--------|------|-------------|
| `event_date` | date | Parsed date from `hour` |
| `event_hour` | integer | Parsed hour (0–23) from `hour` |

---

## Source: Hillstrom Email Marketing Data

**File:** `data/raw/hillstrom_email.csv`  
**Status:** Pending acquisition

| Column | Type | Description |
|--------|------|-------------|
| `recency` | integer | Months since last purchase |
| `history_segment` | categorical | Purchase history segment |
| `history` | numeric | Historical purchase amount |
| `mens` | integer (0/1) | Purchased men's merchandise |
| `womens` | integer (0/1) | Purchased women's merchandise |
| `zip_code` | categorical | Customer zip code type (Urban, Suburban, Rural) |
| `newbie` | integer (0/1) | New customer flag |
| `channel` | categorical | Marketing channel |
| `segment` | categorical | Experiment group (Control, Mens E-Mail, Womens E-Mail) |
| `visit` | integer (0/1) | Whether customer visited within 2 weeks |
| `spend` | numeric | Amount spent within 2 weeks |

### Standardized Fields (after cleaning)

| Column | Type | Description |
|--------|------|-------------|
| `treatment_group` | categorical | Standardized segment label |
| `converted` | integer (0/1) | Alias for `visit` |
| `revenue` | numeric | Alias for `spend` |

---

## DuckDB Tables

**Database:** `data/processed/marketing_analytics.duckdb`  
**Status:** Pending setup

| Table | Layer | Description |
|-------|-------|-------------|
| `raw_avazu_ads` | Raw | Loaded Avazu source data |
| `raw_hillstrom_email` | Raw | Loaded Hillstrom source data |
| `stg_ad_events` | Staging | Cleaned, typed Avazu events |
| `stg_email_experiment` | Staging | Cleaned, typed Hillstrom experiment |
| `mart_campaign_kpis` | Mart | Campaign-level impressions, clicks, CTR |
| `mart_ctr_trends` | Mart | Daily/hourly CTR time series |
| `mart_device_app_performance` | Mart | Segment performance by device and app |
| `mart_ab_test_results` | Mart | A/B test lift and significance |
| `mart_forecast_inputs` | Mart | Time series input for forecasting |
| `mart_forecast_results` | Mart | Actual vs forecast with error metrics |

---

## Export Files (for Tableau / Excel)

| File | Source Mart | Description |
|------|-------------|-------------|
| `data/marts/campaign_kpis.csv` | `mart_campaign_kpis` | Campaign performance summary |
| `data/marts/ctr_trends.csv` | `mart_ctr_trends` | CTR over time |
| `data/marts/segment_performance.csv` | `mart_device_app_performance` | Segment rankings |
| `data/marts/ab_test_results.csv` | `mart_ab_test_results` | Experiment outcomes |
| `data/marts/forecast_results.csv` | `mart_forecast_results` | Forecast accuracy |
| `data/marts/recommendation_matrix.csv` | Derived | Scale / pause / retest actions |

> This dictionary will be updated after Day 2 profiling with actual row counts, date ranges, and data quality findings.
