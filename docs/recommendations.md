# Marketing Recommendations

Evidence-based **scale / pause / retest** actions from populated Week 2 analytics marts.

**Generated:** 2026-07-07 18:43 UTC

---

## Summary

| Action | Count |
|--------|------:|
| Scale | 6 |
| Pause | 3 |
| Retest | 1 |

Portfolio CTR: **16.4074%** on **500,000** impressions
and **82,037** clicks.

---

## Recommendation matrix

| Channel | Segment | Metric | Action | Evidence | Caveat |
|---------|---------|--------|--------|----------|--------|
| Mobile display (Avazu) | device=1 | app=07d7df22 | site=f028772b | banner=1 | CTR | **Scale** | 25.25% CTR on 68,033 impressions (20.9% click share) | Competition subsample; validate on live inventory before budget shifts. |
| Mobile display (Avazu) | device=1 | app=07d7df22 | site=3e814130 | banner=0 | CTR | **Scale** | 22.96% CTR on 35,329 impressions (9.9% click share) | Competition subsample; validate on live inventory before budget shifts. |
| Mobile display (Avazu) | device=0 | app=07d7df22 | site=50e219e0 | banner=0 | CTR | **Scale** | 21.71% CTR on 15,617 impressions (4.1% click share) | Competition subsample; validate on live inventory before budget shifts. |
| Mobile display (Avazu) | device=1 | app=07d7df22 | site=f66779e6 | banner=0 | CTR | **Pause** | 2.67% CTR on 2,807 impressions vs 16.41% portfolio CTR | Confirm spend concentration before pausing; segment still has material volume. |
| Mobile display (Avazu) | device=1 | app=07d7df22 | site=0569f928 | banner=1 | CTR | **Pause** | 3.58% CTR on 2,511 impressions vs 16.41% portfolio CTR | Confirm spend concentration before pausing; segment still has material volume. |
| Mobile display (Avazu) | device=1 | app=07d7df22 | site=76b2941d | banner=0 | CTR | **Pause** | 4.25% CTR on 5,974 impressions vs 16.41% portfolio CTR | Confirm spend concentration before pausing; segment still has material volume. |
| Mobile display (Avazu) | Hour 00 | Hourly CTR | **Scale** | 17.47% CTR with 119,006 impressions | Single-day sample; confirm hour-of-day pattern across more dates. |
| Email (Hillstrom) | Mens E-Mail | Visit conversion rate | **Scale** | +7.66% absolute lift (72.1% relative), p=5.685e-112, incremental revenue $16,403 |  |
| Email (Hillstrom) | Womens E-Mail | Visit conversion rate | **Scale** | +4.52% absolute lift (42.6% relative), p=3.182e-44, incremental revenue $9,077 |  |
| Mobile display (Avazu) | Hourly click forecast | Forecast accuracy (MAPE) | **Retest** | Model moving_average_3: MAE=19,203.0, RMSE=19,203.0, MAPE=314.4% | Single-day holdout only; use forecasts for directional planning. |

---

## Decision rules used

| Action | Rule |
|--------|------|
| **Scale** | Segment CTR ≥ 115% of portfolio CTR with ≥ 1,000 impressions, or significant positive email lift |
| **Pause** | Segment CTR ≤ 75% of portfolio CTR with sufficient volume, or negative email lift |
| **Retest** | Non-significant email treatments or forecast MAPE ≥ 100% |

See [business_problem.md](business_problem.md) and [metric_definitions.md](metric_definitions.md).

---

## Regenerate

```bash
python scripts/generate_recommendations.py
```

Requires all six mart tables populated and `data/processed/marketing_analytics.duckdb` available locally.
