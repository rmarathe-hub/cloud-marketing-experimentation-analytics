# Portfolio Completion Checklist

Final closure document for the Cloud Marketing Experimentation & Forecasting Analytics project.

**Status:** Complete (Days 1–21)

---

## Pipeline deliverables

| Layer | Status | Evidence |
|-------|--------|----------|
| Data foundation (Week 1) | ✅ | `docs/week1_data_lock.md`, 25 validation checks |
| Analytics marts (Week 2) | ✅ | `docs/week2_analytics_lock.md`, 6 mart tables |
| CSV exports | ✅ | `data/exports/*.csv` (local, gitignored) |
| Tableau screenshots | ✅ | `tableau/screenshots/` (6 PNG pages) |
| Excel screenshots | ✅ | `excel/screenshots/` (6 PNG pages) |
| README case study | ✅ | Key Findings section with locked metrics |
| pytest suite | ✅ | 1,700+ tests, default run excludes network/AWS |

---

## Tracked portfolio artifacts

These are the GitHub-visible deliverables reviewers should open first:

1. [README.md](../README.md) — architecture, screenshots, case study
2. `tableau/screenshots/*.png` — Tableau dashboard views
3. `excel/screenshots/*.png` — Excel stakeholder workbook views
4. [recommendations.md](recommendations.md) + [executive_summary.md](executive_summary.md)
5. [resume_bullets.md](resume_bullets.md) + [interview_prep.md](interview_prep.md)

**Not tracked (local/gitignored):** `.env`, raw/processed data, DuckDB file, `.twbx`, `.xlsx`

---

## Locked headline metrics

| Metric | Value |
|--------|-------|
| Avazu impressions | 500,000 |
| Avazu clicks | 82,037 |
| Portfolio CTR | 16.41% |
| Top segment CTR | 25.25% (68,033 impressions) |
| Mens email lift | +7.66 pp (~$16,403 incremental) |
| Womens email lift | +4.52 pp (~$9,077 incremental) |
| Forecast MAPE | 314.4% (single-day caveat) |
| Recommendations | 10 (6 scale, 3 pause, 1 retest) |

---

## Final validation commands

```bash
pytest -q -m "not network and not slow"
pytest -q -m docs
pytest -q -m hygiene
pytest -q -m security
pytest -q -m week2
pytest -q -m tableau
pytest -q -m excel
pytest -q -m portfolio
pytest -q
```

---

## Change policy

1. Re-run the full pipeline before changing locked mart logic.
2. Regenerate lock docs with `generate_week1_data_lock.py` / `generate_week2_analytics_lock.py`.
3. Regenerate screenshots after export changes:
   - `python scripts/build_tableau_dashboard.py`
   - `python scripts/build_excel_workbook_screenshots.py`
4. Re-run pytest before any portfolio commit.
