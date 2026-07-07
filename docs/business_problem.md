# Business Problem

## Context

A marketing analytics team manages two channels with different measurement needs:

1. **Mobile display advertising (Avazu)** — High-volume ad impressions with click/no-click outcomes. The team needs to understand which segments (device, app, site, time) drive engagement and where spend is underperforming.

2. **Email campaigns (Hillstrom)** — A controlled experiment comparing email treatments against a holdout control group. Leadership needs to know whether the treatment drove statistically significant lift in conversions and revenue before scaling.

## Stakeholders

| Stakeholder | Need |
|-------------|------|
| **Marketing Manager** | Which campaigns and segments to scale or pause |
| **Growth Analyst** | CTR trends, segment benchmarks, forecasted demand |
| **Email Marketing Lead** | A/B test results with confidence intervals and retest guidance |
| **Executive Sponsor** | Clear scale / pause / retest recommendations with evidence |

## Core Business Questions

1. Which mobile ad segments drive the highest click-through rate?
2. Does email treatment create statistically significant lift over control?
3. How do engagement patterns vary by hour, day, device, and app?
4. What are near-term click and CTR forecasts for planning?
5. What specific actions should marketing take next?

## Decision Framework

Every recommendation in this project maps to one of three actions:

| Action | When to use |
|--------|-------------|
| **Scale** | Segment or treatment shows strong, statistically supported performance |
| **Pause** | Segment shows consistently low CTR or negative ROI signals |
| **Retest** | Results are inconclusive, underpowered, or limited to a narrow segment |

## Success Criteria

A successful analysis delivers:

- Segment-level CTR rankings with supporting volume
- A/B test results with p-values and 95% confidence intervals
- Forecast accuracy metrics (MAE, RMSE, MAPE) on holdout data
- A recommendation matrix linking evidence to action
- Stakeholder-ready Tableau dashboard and Excel workbook

## Constraints

- Real data only — no synthetic experiment layers
- Cost-safe AWS usage (S3 only, budget alerts)
- Local DuckDB for SQL analytics (no paid warehouse required)
- Analysis must be reproducible via scripts and version-controlled SQL
