# Tableau Dashboard

Six-page marketing analytics dashboard for Avazu mobile display and Hillstrom email experiment data.

---

## Quick start

```bash
# 1. Ensure mart exports exist
python scripts/export_dashboard_data.py

# 2. Generate reference screenshots + build spec
python scripts/build_tableau_dashboard.py
```

---

## Contents

| Path | Description |
|------|-------------|
| `screenshots/` | Six dashboard page PNGs for README and portfolio |
| `dashboard_spec.json` | Page-to-data mapping and Tableau build metadata |
| `marketing_analytics_dashboard.twbx` | Packaged workbook (local only, not committed) |

---

## Dashboard pages

1. **Executive overview** — portfolio KPIs and recommendation mix
2. **CTR trends** — hourly impressions and CTR
3. **Segment performance** — top CTR segments (≥1,000 impressions)
4. **A/B test results** — Hillstrom email lift and significance
5. **Forecast** — holdout click forecast vs actual
6. **Recommendations** — scale / pause / retest matrix

---

## Build in Tableau Desktop

See [docs/tableau_dashboard_guide.md](../docs/tableau_dashboard_guide.md) for step-by-step workbook instructions.

Data source: `data/exports/*.csv` (see `data/exports/tableau_data_manifest.json`).

---

## Screenshots

![Executive overview](screenshots/01_executive_overview.png)

![CTR trends](screenshots/02_ctr_trends.png)

![Segment performance](screenshots/03_segment_performance.png)

![A/B test results](screenshots/04_ab_test_results.png)

![Forecast](screenshots/05_forecast.png)

![Recommendations](screenshots/06_recommendations.png)
