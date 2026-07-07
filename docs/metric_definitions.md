# Metric Definitions

All metrics used across SQL marts, Tableau dashboards, and the Excel workbook.

---

## Campaign Metrics (Avazu)

| Metric | Formula | Notes |
|--------|---------|-------|
| **Impressions** | `COUNT(*)` per segment/time grain | Each row is an ad impression event |
| **Clicks** | `SUM(click)` where click ∈ {0, 1} | Binary click indicator |
| **CTR** | `Clicks / Impressions` | Expressed as decimal or percentage |
| **Click Share** | `Segment Clicks / Total Clicks` | Share of total click volume |
| **Hourly CTR** | CTR aggregated by `event_hour` | Intraday engagement pattern |
| **Daily CTR** | CTR aggregated by `event_date` | Day-over-day trend |

---

## Segmentation Dimensions (Avazu)

| Dimension | Description |
|-----------|-------------|
| `device_type` | Mobile device category (phone, tablet, etc.) |
| `app_category` | Application category |
| `site_category` | Publisher site category |
| `banner_position` | Ad placement position (if available) |
| `event_hour` | Hour of day (0–23) |
| `event_date` | Calendar date of impression |

---

## Experiment Metrics (Hillstrom)

| Metric | Formula | Notes |
|--------|---------|-------|
| **Recipients** | `COUNT(*)` per segment | Total customers in group |
| **Conversions** | `SUM(converted)` or visit indicator | Depends on field available |
| **Conversion Rate** | `Conversions / Recipients` | Primary A/B outcome |
| **Total Revenue** | `SUM(revenue)` per group | Dollar outcome |
| **Revenue per Customer** | `Total Revenue / Recipients` | Normalized revenue metric |
| **Spend** | `SUM(spend)` per group | Campaign cost (if available) |

---

## A/B Test Statistics (Hillstrom)

| Metric | Formula | Notes |
|--------|---------|-------|
| **Absolute Lift** | `Treatment Rate − Control Rate` | Raw difference |
| **Relative Lift %** | `(Treatment − Control) / Control × 100` | Percentage improvement |
| **Incremental Revenue** | `(Treatment Rev/Customer − Control Rev/Customer) × Treatment N` | Estimated added revenue |
| **p-value** | Two-proportion z-test or chi-square | Significance threshold: α = 0.05 |
| **95% Confidence Interval** | `Lift ± 1.96 × SE` | Range of plausible true lift |
| **Statistically Significant** | `p-value < 0.05` | Binary significance flag |

### Treatment Groups

| Group | Description |
|-------|-------------|
| **Control** | No email sent (holdout) |
| **Mens E-Mail** | Male-targeted email treatment |
| **Womens E-Mail** | Female-targeted email treatment |

---

## Forecasting Metrics

| Metric | Formula | Notes |
|--------|---------|-------|
| **MAE** | `mean(|actual − forecast|)` | Mean absolute error |
| **RMSE** | `sqrt(mean((actual − forecast)²))` | Penalizes large errors |
| **MAPE** | `mean(|actual − forecast| / actual) × 100` | Percentage error; undefined when actual = 0 |

### Forecast Models

| Model | Description |
|-------|-------------|
| **Moving Average** | Rolling mean of prior N periods |
| **Seasonal Naive** | Prior period value as forecast |
| **Exponential Smoothing** | Weighted average with decay on prior values |

---

## Recommendation Matrix Fields

| Field | Description |
|-------|-------------|
| `segment` | Device, app, treatment group, or time window |
| `metric` | Primary KPI (CTR, conversion rate, revenue lift) |
| `evidence` | Supporting statistic or chart reference |
| `action` | Scale / Pause / Retest |
| `caveat` | Sample size, seasonality, or significance limitation |
