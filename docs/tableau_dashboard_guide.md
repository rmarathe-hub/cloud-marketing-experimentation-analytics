# Tableau Dashboard Guide

Portfolio deliverable for Phase 3 Tableau work: **six dashboard PNG screenshots** in `tableau/screenshots/`, built from DuckDB mart CSV exports.

---

## Deliverable model

| Artifact | Tracked in Git? | Role |
|----------|-----------------|------|
| `tableau/screenshots/*.png` | **Yes** | Official portfolio deliverable (README + GitHub) |
| `data/exports/*.csv` | No (gitignored) | Pipeline input; regenerate locally |
| `tableau/marketing_analytics_dashboard.twbx` | **No** (gitignored) | Optional local workbook; may be rebuilt manually |
| `tableau/dashboard_spec.json` | Yes | Page-to-data mapping metadata |

The Tableau packaged workbook is **local-only, gitignored, and optional**. It is not required to reproduce the analytics pipeline. If a local `.twbx` has a broken Clipboard data source, that does not affect the screenshot deliverable.

Screenshot PNGs are the version-controlled artifact reviewers should use.

---

## Data source folder

```
data/exports/
```

Input CSVs (from `python scripts/export_dashboard_data.py`):

| CSV | Dashboard page |
|-----|----------------|
| `campaign_kpis.csv` | Executive overview |
| `ctr_trends.csv` | CTR trends by hour |
| `segment_performance.csv` | Segment performance |
| `ab_test_results.csv` | Email A/B test results |
| `forecast_results.csv` | Click forecast |
| `recommendation_matrix.csv` | Recommendations matrix |

Manifest: `data/exports/tableau_data_manifest.json`

---

## Screenshot folder

```
tableau/screenshots/
```

Required files:

1. `01_executive_overview.png`
2. `02_ctr_trends.png`
3. `03_segment_performance.png`
4. `04_ab_test_results.png`
5. `05_forecast.png`
6. `06_recommendations.png`

Regenerate from exports:

```bash
python scripts/export_dashboard_data.py
python scripts/build_tableau_dashboard.py
```

---

## Forecast caveat

**MAPE 314.4%** on the holdout forecast is **directional only** because the Avazu source data is a **single-day** sample with hourly aggregation. Do not treat the forecast as production-grade or reliable for deployment budgeting without additional dates.

---

## Optional: rebuild workbook in Tableau Desktop

If you want a local `.twbx` for exploration:

1. Open Tableau Desktop → **Connect** → **Text file**
2. Add all six CSVs from `data/exports/`
3. Build six dashboard pages matching the screenshot references
4. Save as `tableau/marketing_analytics_dashboard.twbx` (gitignored, not committed)

Page build notes:

### Page 1 — Executive overview
- Number cards: impressions, clicks, CTR (`campaign_kpis.csv`)
- Bar chart: recommendation counts by `action` (`recommendation_matrix.csv`)
- Reference: `tableau/screenshots/01_executive_overview.png`

### Page 2 — CTR trends by hour
- Dual-axis: bar = impressions, line = CTR (`ctr_trends.csv`)
- X-axis: `event_hour` (ascending)
- Reference: `tableau/screenshots/02_ctr_trends.png`

### Page 3 — Segment performance
- Horizontal bar: CTR by segment (`segment_performance.csv`)
- Filter: `impressions >= 1000`, top 10 by CTR
- Reference line: portfolio CTR 16.41%
- Reference: `tableau/screenshots/03_segment_performance.png`

### Page 4 — Email A/B test results
- Bar: conversion rate by `treatment_label` (`ab_test_results.csv`)
- Second chart: absolute lift (exclude control)
- Reference: `tableau/screenshots/04_ab_test_results.png`

### Page 5 — Click forecast
- Bar: actual vs forecast clicks (`forecast_results.csv`)
- Caption: model name, MAPE, single-day caveat
- Reference: `tableau/screenshots/05_forecast.png`

### Page 6 — Recommendations matrix
- Bar: count by `action`
- Table: channel, segment, metric, action, evidence
- Reference: `tableau/screenshots/06_recommendations.png`

---

## Locked production metrics (sanity check)

| Metric | Expected |
|--------|----------|
| Portfolio impressions | 500,000 |
| Portfolio CTR | 16.41% |
| Mens email lift | +7.66 pp (significant) |
| Womens email lift | +4.52 pp (significant) |
| Top segment CTR | 25.25% |
| Forecast MAPE | 314.4% (single-day caveat) |
| Recommendations | 10 (6 scale, 3 pause, 1 retest) |

See [week2_analytics_lock.md](week2_analytics_lock.md) for full locked stats.
