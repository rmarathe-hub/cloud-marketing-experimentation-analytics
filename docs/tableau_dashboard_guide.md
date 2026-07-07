# Tableau Dashboard Build Guide

Step-by-step instructions for building the **6-page marketing analytics dashboard** in Tableau Desktop using the exported mart CSVs.

---

## Prerequisites

1. Week 2 exports exist locally:

```bash
python scripts/export_dashboard_data.py
```

2. Reference screenshots generated (optional but recommended):

```bash
python scripts/build_tableau_dashboard.py
```

3. Tableau Desktop installed (2022.1+ recommended).

---

## Data connection

1. Open Tableau Desktop → **Connect** → **Text file**.
2. Point to `data/exports/` and add all six CSVs:

| CSV | Dashboard page |
|-----|----------------|
| `campaign_kpis.csv` | Executive overview |
| `ctr_trends.csv` | CTR trends by hour |
| `segment_performance.csv` | Segment performance |
| `ab_test_results.csv` | Email A/B test results |
| `forecast_results.csv` | Click forecast |
| `recommendation_matrix.csv` | Recommendations matrix |

Manifest reference: `data/exports/tableau_data_manifest.json`

---

## Page 1 — Executive overview

**Sheet:** `Executive KPIs`

- **Number cards:** impressions, clicks, CTR (`campaign_kpis.csv`)
- **Bar chart:** recommendation counts by action (`recommendation_matrix.csv`, COUNT by `action`)
- **Filter:** none (portfolio-level)

Match reference: `tableau/screenshots/01_executive_overview.png`

---

## Page 2 — CTR trends by hour

**Sheet:** `Hourly CTR`

- **Dual-axis chart:** bar = impressions, line = CTR (`ctr_trends.csv`)
- **X-axis:** `event_hour`
- **Sort:** ascending hour

Match reference: `tableau/screenshots/02_ctr_trends.png`

---

## Page 3 — Segment performance

**Sheet:** `Top Segments`

- **Horizontal bar:** CTR by segment (`segment_performance.csv`)
- **Filter:** `impressions >= 1000`
- **Top N:** 10 by CTR
- **Reference line:** portfolio CTR 16.41%

Match reference: `tableau/screenshots/03_segment_performance.png`

---

## Page 4 — Email A/B test results

**Sheet:** `AB Test Lift`

- **Bar chart:** conversion rate by `treatment_label` (`ab_test_results.csv`)
- **Second chart:** absolute lift for treatment rows (exclude control)
- **Annotation:** p-value and significance flag

Match reference: `tableau/screenshots/04_ab_test_results.png`

---

## Page 5 — Click forecast

**Sheet:** `Forecast Holdout`

- **Bar chart:** actual vs forecast clicks (`forecast_results.csv`)
- **Caption:** model name, MAPE, single-day holdout caveat

Match reference: `tableau/screenshots/05_forecast.png`

---

## Page 6 — Recommendations matrix

**Sheet:** `Recommendation Actions`

- **Bar chart:** count by `action`
- **Table:** channel, segment, metric, action, evidence (`recommendation_matrix.csv`)

Match reference: `tableau/screenshots/06_recommendations.png`

---

## Dashboard assembly

1. Create a new dashboard for each page (6 total).
2. Add navigation tabs: Executive → Trends → Segments → A/B Test → Forecast → Recommendations.
3. Use a consistent color palette:
   - Scale: green `#2d6a4f`
   - Pause: red `#bc4749`
   - Retest: gold `#e9c46a`
   - Primary: navy `#1f4e79`

---

## Save workbook

Save as a **packaged workbook** (local only, gitignored):

```
tableau/marketing_analytics_dashboard.twbx
```

The repository tracks screenshots and build spec only — not the `.twbx` file.

---

## Regenerate screenshots

After export data changes:

```bash
python scripts/build_tableau_dashboard.py
```

Outputs:

- `tableau/screenshots/*.png` (6 pages)
- `tableau/dashboard_spec.json`
- `data/processed/tableau_build_summary.json`

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
