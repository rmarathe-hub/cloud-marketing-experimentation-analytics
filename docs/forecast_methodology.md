# CTR Forecast Methodology (Avazu Hourly Trends)

Forecasting approach for near-term click volume and CTR using cleaned ad event staging data.

---

## Scope and caveat

Avazu in this project is a **single-day competition subsample** (2014-10-21). Forecasting here
demonstrates the analytics workflow (train/holdout split, accuracy metrics, mart outputs) rather
than production media-buy forecasting across multiple days.

---

## Input series

| Source | Mart |
|--------|------|
| `stg_ad_events` | `mart_forecast_inputs` |

Hourly grain: `event_date`, `event_hour`, `impressions`, `clicks`, `ctr`.

---

## Models evaluated

| Model | Description |
|-------|-------------|
| `moving_average_3` | 3-period moving average of prior hourly clicks/CTR |
| `naive_last_hour` | Previous hour actual as forecast |

The script selects the model with the lowest holdout **MAE** on clicks and writes that model's
holdout predictions to `mart_forecast_results`.

---

## Holdout design

| Setting | Default |
|---------|---------|
| Minimum series length | 3 hourly observations |
| Holdout window | 1 hour (or fewer if series is short) |
| Training window | All prior hourly rows |

---

## Accuracy metrics

| Metric | Formula |
|--------|---------|
| MAE | `mean(|actual_clicks - forecast_clicks|)` |
| RMSE | `sqrt(mean((actual_clicks - forecast_clicks)^2))` |
| MAPE | `mean(|actual - forecast| / actual) * 100` (clicks; skips actual=0) |

Metrics are stored in `mart_forecast_results` and `data/processed/forecast_summary.json`.

---

## Outputs

| Artifact | Location |
|----------|----------|
| Forecast inputs mart | `mart_forecast_inputs` |
| Forecast results mart | `mart_forecast_results` |
| Run summary | `data/processed/forecast_summary.json` |
| Builder script | `scripts/run_ctr_forecast.py` |

See [metric_definitions.md](metric_definitions.md) for metric definitions used in dashboards.
