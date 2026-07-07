# Tableau Dashboard

Six-page marketing analytics dashboard for Avazu mobile display and Hillstrom email experiment data.

**Portfolio deliverable:** the six PNG screenshots in `screenshots/` (tracked in Git). The `.twbx` workbook is local/gitignored and optional.

---

## Screenshots (official deliverable)

| File | Page |
|------|------|
| `screenshots/01_executive_overview.png` | Executive overview |
| `screenshots/02_ctr_trends.png` | CTR trends by hour |
| `screenshots/03_segment_performance.png` | Segment performance |
| `screenshots/04_ab_test_results.png` | Email A/B test results |
| `screenshots/05_forecast.png` | Click forecast |
| `screenshots/06_recommendations.png` | Recommendations matrix |

---

## Data inputs

Source folder: `data/exports/` (six CSVs from `export_dashboard_data.py`).

See [docs/tableau_dashboard_guide.md](../docs/tableau_dashboard_guide.md) for full documentation.

---

## Regenerate screenshots

```bash
python scripts/export_dashboard_data.py
python scripts/build_tableau_dashboard.py
```

---

## Local workbook (optional, not committed)

`marketing_analytics_dashboard.twbx` may exist locally for Tableau Desktop exploration. It is gitignored and not part of the repository deliverable. Rebuild from CSV exports if needed.
