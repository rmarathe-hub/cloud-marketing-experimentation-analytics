# Excel Executive Workbook Guide

Portfolio deliverable for Phase 3 Excel work: **six workbook PNG screenshots** in `excel/screenshots/`, built from DuckDB mart CSV exports.

---

## Deliverable model

| Artifact | Tracked in Git? | Role |
|----------|-----------------|------|
| `excel/screenshots/*.png` | **Yes** | Official portfolio deliverable (README + GitHub) |
| `data/exports/*.csv` | No (gitignored) | Pipeline input; regenerate locally |
| `excel/marketing_executive_workbook.xlsx` | **No** (gitignored) | Optional local workbook for stakeholder editing |

The Excel workbook is **local-only, gitignored, and optional**. It is not required to reproduce the analytics pipeline. Screenshot PNGs are the version-controlled artifact reviewers should use.

---

## Data source folder

```
data/exports/
```

Input CSVs (from `python scripts/export_dashboard_data.py`):

| CSV | Workbook sheet |
|-----|----------------|
| `campaign_kpis.csv` | Campaign_KPIs, Executive_Summary |
| `ctr_trends.csv` | CTR_Trends |
| `segment_performance.csv` | Segment_Performance |
| `ab_test_results.csv` | AB_Test_Results, AB_Calculator |
| `forecast_results.csv` | Forecast_Results |
| `recommendation_matrix.csv` | Recommendations, Pivot_Recommendations |

---

## Screenshot folder

```
excel/screenshots/
```

Required files:

1. `01_executive_summary.png`
2. `02_campaign_kpis.png`
3. `03_ab_test_results.png`
4. `04_recommendations.png`
5. `05_pivot_recommendations.png`
6. `06_ab_calculator.png`

Regenerate:

```bash
python scripts/export_dashboard_data.py
python scripts/build_excel_workbook_screenshots.py
```

---

## Polished workbook (local)

`export_dashboard_data.py` writes a stakeholder workbook with:

- **Executive_Summary** — formatted KPI overview
- **Data sheets** — mart tables with styled headers and frozen panes
- **Pivot_Recommendations** — action-count pivot with embedded bar chart
- **AB_Calculator** — scenario formulas for conversion-rate what-if analysis

Save path (gitignored):

```
excel/marketing_executive_workbook.xlsx
```

---

## Forecast caveat

**MAPE 314.4%** on the holdout forecast is **directional only** because the Avazu source data is a **single-day** sample. Do not treat forecast outputs as production-grade deployment signals.

---

## Locked production metrics (sanity check)

| Metric | Expected |
|--------|----------|
| Portfolio impressions | 500,000 |
| Portfolio CTR | 16.41% |
| Mens email lift | +7.66 pp (significant) |
| Womens email lift | +4.52 pp (significant) |
| Recommendations | 10 (6 scale, 3 pause, 1 retest) |

See [week2_analytics_lock.md](week2_analytics_lock.md) for full locked stats.
