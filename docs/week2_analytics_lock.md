# Week 2 Analytics Lock

**Status:** Locked  
**Generated:** 2026-07-07T18:55:36.963255+00:00  
**Scope:** Days 8–13 marketing analytics, recommendations, and BI exports

This document freezes verified Week 2 mart statistics, experiment outcomes, forecast metrics, recommendations, and export inventory. Do not change locked values in downstream docs without re-running the full Week 2 pipeline and regenerating this file.

---

## Locked headline metrics

| Metric | Locked value |
|--------|--------------|
| Portfolio CTR | 16.4074% |
| Impressions | 500,000 |
| Clicks | 82,037 |
| Top segment CTR | 25.25% on 68,033 impressions |
| Mens E-Mail absolute lift | 7.66% |
| Womens E-Mail absolute lift | 4.52% |
| Forecast model | moving_average_3 |
| Forecast MAPE | 314.4% |
| Recommendations | 10 (scale=6, pause=3, retest=1) |
| CSV exports | 6 files |

---

## Mart table inventory

Database: `data/processed/marketing_analytics.duckdb`

- `mart_campaign_kpis`: 1 rows
- `mart_ctr_trends`: 4 rows
- `mart_device_app_performance`: 83 rows
- `mart_ab_test_results`: 3 rows
- `mart_forecast_inputs`: 4 rows
- `mart_forecast_results`: 1 rows

---

## A/B test outcomes (Hillstrom)

| Treatment | Recipients | Conversion rate | Absolute lift | Statistically significant |
|-----------|------------|-----------------|---------------|---------------------------|
| control | 21,306 | 10.6167% | 0.00% | — |
| mens_email | 21,307 | 18.2757% | 7.66% | True |
| womens_email | 21,387 | 15.1400% | 4.52% | True |

Significant treatments: mens_email, womens_email

---

## Forecast accuracy

| Model | MAE | RMSE | MAPE |
|-------|-----|------|------|
| moving_average_3 (selected) | 19,203.0 | 19,203.0 | 314.4% |

Holdout hours: 1 | Train hours: 3

---

## Export inventory

Excel workbook: `excel/marketing_executive_workbook.xlsx`  
Tableau manifest: `data/exports/tableau_data_manifest.json`

- `campaign_kpis.csv`: 1 rows (Campaign KPIs)
- `ctr_trends.csv`: 4 rows (CTR trends)
- `segment_performance.csv`: 83 rows (Segment performance)
- `ab_test_results.csv`: 3 rows (A/B test results)
- `forecast_results.csv`: 1 rows (Forecast results)
- `recommendation_matrix.csv`: 10 rows (Scale / pause / retest recommendation matrix)

---

## Week 2 pipeline (frozen order)

1. `python scripts/run_campaign_kpis.py`
2. `python scripts/run_funnel_segment_analysis.py`
3. `python scripts/run_ab_test_analysis.py`
4. `python scripts/run_ctr_forecast.py`
5. `python scripts/generate_recommendations.py`
6. `python scripts/export_dashboard_data.py`
7. `python scripts/validate_data.py`

Regenerate this lock after any analytics logic change:

```bash
python scripts/generate_week2_analytics_lock.py
```

---

## Validation status

Validation success: **True**  
Checks passed: **25 / 25**

- raw_avazu_ads_row_count: pass
- raw_hillstrom_email_row_count: pass
- stg_ad_events_row_count: pass
- stg_email_experiment_row_count: pass
- stg_ad_events_ctr: pass
- stg_email_experiment_visit_rate: pass
- stg_email_experiment_treatment_groups: pass
- mart_campaign_kpis_populated: pass
- mart_campaign_kpis_ctr: pass
- mart_ctr_trends_populated: pass
- mart_ctr_trends_impressions: pass
- mart_ctr_trends_ctr: pass
- mart_device_app_performance_populated: pass
- mart_device_app_performance_impressions: pass
- mart_device_app_performance_click_share: pass
- mart_ab_test_results_populated: pass
- mart_ab_test_results_group_counts: pass
- mart_ab_test_results_recipients: pass
- mart_ab_test_results_overall_conversion_rate: pass
- mart_ab_test_results_treatment_significance: pass
- mart_forecast_inputs_populated: pass
- mart_forecast_inputs_impressions: pass
- mart_forecast_inputs_ctr: pass
- mart_forecast_results_populated: pass
- mart_forecast_results_metrics: pass

---

## Change policy

1. Do not edit locked statistics manually in stakeholder docs.
2. Re-run the full Week 2 pipeline if mart logic or source data changes.
3. Regenerate this document with `generate_week2_analytics_lock.py`.
4. Re-run `pytest -q` after any pipeline or portfolio doc changes.

---

## Phase 3 boundary

All Phase 3 portfolio deliverables are **complete**:

- Tableau dashboard screenshots (6 PNG pages) — `tableau/screenshots/`, `docs/tableau_dashboard_guide.md`
- Excel workbook screenshots (6 PNG pages) — `excel/screenshots/`, `docs/excel_workbook_guide.md`
- Final README case study — Key Findings section in README
- Final tests + cleanup — `docs/portfolio_completion.md`
- Resume / interview prep — `docs/resume_bullets.md`, `docs/interview_prep.md`, `docs/linkedin_summary.md`

The Tableau `.twbx` and Excel `.xlsx` workbooks are local/gitignored and optional; PNG screenshots are the tracked portfolio artifacts.
