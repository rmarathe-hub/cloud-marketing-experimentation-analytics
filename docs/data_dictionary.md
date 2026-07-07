# Data Dictionary

Column-level reference for source datasets and analytical marts. Updated after Day 2 profiling.

---

## Source: Avazu Mobile Ad Click Data

**File:** `data/raw/avazu_train.csv`  
**Status:** Acquired (500,000-row real subsample from Kaggle competition data)  
**Profiled:** 2026-07-07

| Stat | Value |
|------|-------|
| Rows | 500,000 |
| Date range | 2014-10-21 (1 day in subsample) |
| CTR | 16.41% |
| Clicks | 82,037 |
| Impressions | 500,000 |
| Missing values | None detected |

> Note: The Avazu competition dataset uses click/non-click subsampling, so CTR is not representative of live display advertising rates.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer | Unique impression identifier |
| `click` | integer (0/1) | Whether the ad was clicked |
| `hour` | string | Timestamp encoded as YYMMDDHH |
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
| `C14`–`C21` | numeric | Anonymous features |

### Unique entity counts (profiled)

| Entity | Unique values |
|--------|---------------|
| `device_id` | 41,413 |
| `device_type` | 4 |
| `app_id` | 1,641 |
| `app_category` | 20 |
| `site_id` | 1,704 |
| `site_category` | 21 |
| `banner_pos` | 6 |

### Derived fields (after cleaning)

| Column | Type | Description |
|--------|------|-------------|
| `event_date` | date | Parsed date from `hour` |
| `event_hour` | integer | Parsed hour (0–23) from `hour` |

---

## Source: Hillstrom Email Marketing Data

**File:** `data/raw/hillstrom_email.csv`  
**Status:** Acquired (full 64,000-row dataset from MineThatData)  
**Profiled:** 2026-07-07

| Stat | Value |
|------|-------|
| Rows | 64,000 |
| Visit rate | 14.68% |
| Conversion rate | 0.90% |
| Missing values | None detected |

| Column | Type | Description |
|--------|------|-------------|
| `recency` | integer | Months since last purchase |
| `history_segment` | categorical | Purchase history segment |
| `history` | numeric | Historical purchase amount |
| `mens` | integer (0/1) | Purchased men's merchandise |
| `womens` | integer (0/1) | Purchased women's merchandise |
| `zip_code` | categorical | Urban / Suburban / Rural |
| `newbie` | integer (0/1) | New customer flag |
| `channel` | categorical | Web / Phone / Multichannel |
| `segment` | categorical | No E-Mail / Mens E-Mail / Womens E-Mail |
| `visit` | integer (0/1) | Visited within 2 weeks |
| `conversion` | integer (0/1) | Purchased within 2 weeks |
| `spend` | numeric | Amount spent within 2 weeks |

### Treatment group counts (profiled)

| Segment | Recipients |
|---------|------------|
| Womens E-Mail | 21,387 |
| Mens E-Mail | 21,307 |
| No E-Mail (control) | 21,306 |

### Standardized fields (after cleaning)

| Column | Type | Description |
|--------|------|-------------|
| `treatment_group` | categorical | Standardized segment label |
| `converted` | integer (0/1) | Alias for `visit` |
| `revenue` | numeric | Alias for `spend` |

---

## DuckDB Tables

**Database:** `data/processed/marketing_analytics.duckdb`  
**Status:** Schema created (Day 5). Data loaded and validated (Day 6).

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

## Export files (for Tableau / Excel)

| File | Source mart | Description |
|------|-------------|-------------|
| `data/marts/campaign_kpis.csv` | `mart_campaign_kpis` | Campaign performance summary |
| `data/marts/ctr_trends.csv` | `mart_ctr_trends` | CTR over time |
| `data/marts/segment_performance.csv` | `mart_device_app_performance` | Segment rankings |
| `data/marts/ab_test_results.csv` | `mart_ab_test_results` | Experiment outcomes |
| `data/marts/forecast_results.csv` | `mart_forecast_results` | Forecast accuracy |
| `data/marts/recommendation_matrix.csv` | Derived | Scale / pause / retest actions |

---

## Dataset sources

| Dataset | Source | Acquisition |
|---------|--------|-------------|
| Hillstrom | [MineThatData](http://www.minethatdata.com/Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv) | Auto-download via `scripts/download_or_import_data.py` |
| Avazu | [Kaggle Avazu CTR Prediction](https://www.kaggle.com/competitions/avazu-ctr-prediction) | 500k-row subsample streamed from public mirror; optional full `train.gz` via Kaggle API |

See `data/processed/raw_profile_summary.json` for full profiling output.
