# Excel Executive Workbook

Stakeholder Excel workbook built from DuckDB mart CSV exports.

**Portfolio deliverable:** the six PNG screenshots in `screenshots/` (tracked in Git). The `.xlsx` workbook is local/gitignored and optional.

---

## Screenshots (official deliverable)

| File | Sheet / view |
|------|----------------|
| `screenshots/01_executive_summary.png` | Executive summary KPIs |
| `screenshots/02_campaign_kpis.png` | Campaign KPIs |
| `screenshots/03_ab_test_results.png` | Hillstrom A/B test results |
| `screenshots/04_recommendations.png` | Recommendations matrix |
| `screenshots/05_pivot_recommendations.png` | Pivot by action + chart |
| `screenshots/06_ab_calculator.png` | A/B scenario calculator |

---

## Workbook sheets (local `.xlsx`)

1. `Executive_Summary` — portfolio KPIs and recommendation mix
2. `Campaign_KPIs` — impressions, clicks, CTR
3. `CTR_Trends` — hourly engagement
4. `Segment_Performance` — device/app/site segments
5. `AB_Test_Results` — Hillstrom lift and significance
6. `Forecast_Results` — holdout forecast metrics
7. `Recommendations` — scale / pause / retest matrix
8. `Pivot_Recommendations` — action-count pivot with bar chart
9. `AB_Calculator` — editable scenario formulas

---

## Regenerate

```bash
python scripts/export_dashboard_data.py
python scripts/build_excel_workbook_screenshots.py
```

See [docs/excel_workbook_guide.md](../docs/excel_workbook_guide.md) for full documentation.
