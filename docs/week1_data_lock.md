# Week 1 Data Lock

**Status:** Locked  
**Generated:** 2026-07-07T18:03:15.333596+00:00  
**Scope:** Days 1–6 data foundation (no analytics marts)

This document freezes the verified Week 1 dataset statistics and pipeline outputs. Do not change locked values in downstream docs without re-running the full Week 1 pipeline and regenerating this file.

---

## Locked dataset statistics

### Avazu mobile ads

| Metric | Locked value |
|--------|--------------|
| Raw rows | 500,000 |
| Cleaned rows | 500,000 |
| CTR | 16.4074% |
| Date range | 2014-10-21 to 2014-10-21 |
| Rows removed in cleaning | 0 |

### Hillstrom email experiment

| Metric | Locked value |
|--------|--------------|
| Raw rows | 64,000 |
| Cleaned rows | 64,000 |
| Visit rate | 14.6781% |
| Conversion rate | 0.9031% |
| Rows removed in cleaning | 0 |

### Hillstrom treatment groups (locked)

| Group | Recipients |
|-------|------------|
| control | 21,306 |
| mens_email | 21,307 |
| womens_email | 21,387 |

---

## Week 1 pipeline (frozen order)

1. `python scripts/download_or_import_data.py`
2. `python scripts/profile_raw_data.py`
3. `python scripts/clean_avazu_ads.py`
4. `python scripts/clean_hillstrom_email.py`
5. `python scripts/upload_to_s3.py`
6. `python scripts/create_duckdb_database.py`
7. `python scripts/load_to_duckdb.py`
8. `python scripts/validate_data.py`

Regenerate this lock after any upstream data change:

```bash
python scripts/generate_week1_data_lock.py
```

---

## Local artifacts (gitignored)

| Artifact | Purpose |
|----------|---------|
| `data/raw/avazu_train.csv` | Avazu source |
| `data/raw/hillstrom_email.csv` | Hillstrom source |
| `data/processed/avazu_clean.parquet` | Cleaned Avazu |
| `data/processed/hillstrom_clean.parquet` | Cleaned Hillstrom |
| `data/processed/raw_profile_summary.json` | Profiling output |
| `data/processed/cleaning_summary.json` | Cleaning output |
| `data/processed/marketing_analytics.duckdb` | DuckDB warehouse |
| `data/processed/duckdb_load_summary.json` | Load output |
| `data/processed/data_validation_summary.json` | Validation output |
| `data/processed/s3_upload_summary.json` | S3 upload output |

---

## DuckDB load status

Database: `data/processed/marketing_analytics.duckdb`

- `raw_avazu_ads`: 500,000 rows (success)
- `raw_hillstrom_email`: 64,000 rows (success)
- `stg_ad_events`: 500,000 rows (success)
- `stg_email_experiment`: 64,000 rows (success)

Mart tables remain empty until Week 2 analytics scripts run.

---

## Validation status

Validation success: **True**  
Checks passed: **13 / 13**

- raw_avazu_ads_row_count: pass
- raw_hillstrom_email_row_count: pass
- stg_ad_events_row_count: pass
- stg_email_experiment_row_count: pass
- stg_ad_events_ctr: pass
- stg_email_experiment_visit_rate: pass
- stg_email_experiment_treatment_groups: pass
- mart_campaign_kpis_empty: pass
- mart_ctr_trends_empty: pass
- mart_device_app_performance_empty: pass
- mart_ab_test_results_empty: pass
- mart_forecast_inputs_empty: pass
- mart_forecast_results_empty: pass

---

## S3 upload status

- Bucket: `rmarathe-marketing-analytics-2026`
- Uploaded files: 4
- `raw/avazu_train.csv` (73.76 MB)
- `raw/hillstrom_email.csv` (3.78 MB)
- `processed/avazu_clean.parquet` (16.92 MB)
- `processed/hillstrom_clean.parquet` (0.50 MB)

---

## Change policy

1. Do not edit locked statistics manually in analytics docs.
2. Re-run the full Week 1 pipeline if source data or cleaning logic changes.
3. Regenerate this document with `generate_week1_data_lock.py`.
4. Re-run `pytest -q -m "not network and not slow"` before starting Week 2.

---

## Week 2 boundary

Week 1 ends here. The following are **not started**:

- Campaign KPI marts
- A/B test analysis scripts
- CTR forecasting
- Tableau dashboard
- Excel workbook

Proceed to Week 2 only after this lock document matches your local validation output.
