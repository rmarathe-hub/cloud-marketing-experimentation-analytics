# Executive Summary

One-page stakeholder view of Week 2 marketing analytics findings.

**Generated:** 2026-07-07 18:43 UTC

---

## Headline metrics

1. **Mobile CTR:** 16.4074% across 500,000 impressions (82,037 clicks).
2. **Segment leader:** Top mobile segment CTR **25.25%** on **68,033** impressions (07d7df22 / f028772b).
3. **Email experiment:** Strongest email treatment: **Mens E-Mail** with **+7.66%** absolute visit lift (p=5.685e-112).
4. **Forecast check:** Hourly click forecast MAPE **314.4%** (moving_average_3); treat as directional only on single-day data.
5. **Validation:** Recommendations derived from populated DuckDB marts (`mart_campaign_kpis`, `mart_device_app_performance`, `mart_ab_test_results`, `mart_forecast_results`).

---

## Recommended actions

- **Scale:** device=1 | app=07d7df22 | site=f028772b | banner=1 — 25.25% CTR on 68,033 impressions (20.9% click share)
- **Scale:** device=1 | app=07d7df22 | site=3e814130 | banner=0 — 22.96% CTR on 35,329 impressions (9.9% click share)
- **Scale:** device=0 | app=07d7df22 | site=50e219e0 | banner=0 — 21.71% CTR on 15,617 impressions (4.1% click share)
- **Pause:** device=1 | app=07d7df22 | site=f66779e6 | banner=0 — 2.67% CTR on 2,807 impressions vs 16.41% portfolio CTR
- **Pause:** device=1 | app=07d7df22 | site=0569f928 | banner=1 — 3.58% CTR on 2,511 impressions vs 16.41% portfolio CTR

---

## Caveats

- Avazu is a single-day competition subsample; CTR is not a live campaign benchmark.
- Hillstrom `converted` equals `visit`; revenue uses cleaned `spend`.
- Tableau and Excel portfolio deliverables are complete (screenshot PNGs in `tableau/screenshots/` and `excel/screenshots/`).

Full matrix: [recommendations.md](recommendations.md)
