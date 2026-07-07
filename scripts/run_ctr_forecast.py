#!/usr/bin/env python3
"""Build CTR forecast marts from hourly stg_ad_events trends."""

from __future__ import annotations

import json
import math
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import duckdb

from create_duckdb_database import DatabaseConfig, _display_path, load_config
from paths import FORECAST_SUMMARY

INPUTS_TABLE = "mart_forecast_inputs"
RESULTS_TABLE = "mart_forecast_results"
MIN_SERIES_LENGTH = 2
DEFAULT_HOLDOUT_HOURS = 1
MOVING_AVERAGE_WINDOW = 3
PRIMARY_MODEL_NAME = "moving_average_3"

FORECAST_INPUTS_INSERT_SQL = """
INSERT INTO mart_forecast_inputs (event_date, event_hour, impressions, clicks, ctr)
SELECT
    event_date,
    event_hour,
    COUNT(*)::BIGINT AS impressions,
    SUM(click)::BIGINT AS clicks,
    CASE
        WHEN COUNT(*) = 0 THEN 0.0
        ELSE SUM(click)::DOUBLE / COUNT(*)::DOUBLE
    END AS ctr
FROM stg_ad_events
WHERE event_date IS NOT NULL AND event_hour IS NOT NULL
GROUP BY event_date, event_hour
ORDER BY event_date, event_hour
"""

HOURLY_SERIES_SQL = """
SELECT
    event_date,
    event_hour,
    impressions,
    clicks,
    ctr
FROM mart_forecast_inputs
ORDER BY event_date, event_hour
"""


def ensure_database_ready(config: DatabaseConfig) -> None:
    if not config.database_path.exists():
        raise RuntimeError(
            f"DuckDB database not found at {config.database_path}. "
            "Run create_duckdb_database.py and load_to_duckdb.py first."
        )


def ensure_staging_has_data(connection: duckdb.DuckDBPyConnection) -> int:
    row_count = int(
        connection.execute("SELECT COUNT(*) FROM stg_ad_events").fetchone()[0]
    )
    if row_count == 0:
        raise RuntimeError(
            "stg_ad_events is empty. Run `python scripts/load_to_duckdb.py` first."
        )
    return row_count


def clear_mart_tables(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute(f"DELETE FROM {INPUTS_TABLE}")
    connection.execute(f"DELETE FROM {RESULTS_TABLE}")


def fetch_hourly_series(connection: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    rows = connection.execute(HOURLY_SERIES_SQL).fetchall()
    return [
        {
            "event_date": row[0].isoformat() if isinstance(row[0], date) else str(row[0]),
            "event_hour": int(row[1]),
            "impressions": int(row[2]),
            "clicks": int(row[3]),
            "ctr": float(row[4]),
        }
        for row in rows
    ]


def _moving_average(values: list[float], window: int) -> float:
    if not values:
        return 0.0
    sample = values[-window:]
    return sum(sample) / len(sample)


def _compute_error_metrics(
    actuals: list[float],
    forecasts: list[float],
) -> dict[str, float | None]:
    if not actuals:
        return {"mae": None, "rmse": None, "mape": None}

    abs_errors = [abs(actual - forecast) for actual, forecast in zip(actuals, forecasts)]
    sq_errors = [(actual - forecast) ** 2 for actual, forecast in zip(actuals, forecasts)]
    mae = sum(abs_errors) / len(abs_errors)
    rmse = math.sqrt(sum(sq_errors) / len(sq_errors))

    mape_values = []
    for actual, forecast in zip(actuals, forecasts):
        if actual == 0:
            continue
        mape_values.append(abs(actual - forecast) / actual)
    mape = None if not mape_values else (sum(mape_values) / len(mape_values)) * 100.0

    return {
        "mae": round(mae, 6),
        "rmse": round(rmse, 6),
        "mape": None if mape is None else round(mape, 6),
    }


def build_model_forecasts(
    series: list[dict[str, Any]],
    holdout_hours: int = DEFAULT_HOLDOUT_HOURS,
) -> dict[str, Any]:
    if len(series) < MIN_SERIES_LENGTH:
        raise RuntimeError(
            f"Need at least {MIN_SERIES_LENGTH} hourly observations for forecasting; "
            f"found {len(series)}."
        )

    holdout_hours = max(1, min(holdout_hours, len(series) - 1))
    train_rows = series[:-holdout_hours]
    holdout_rows = series[-holdout_hours:]

    train_clicks = [float(row["clicks"]) for row in train_rows]
    train_ctrs = [float(row["ctr"]) for row in train_rows]

    models: dict[str, list[dict[str, Any]]] = {
        PRIMARY_MODEL_NAME: [],
        "naive_last_hour": [],
    }

    rolling_clicks = train_clicks.copy()
    rolling_ctrs = train_ctrs.copy()
    for row in holdout_rows:
        forecast_clicks = _moving_average(rolling_clicks, MOVING_AVERAGE_WINDOW)
        forecast_ctr = _moving_average(rolling_ctrs, MOVING_AVERAGE_WINDOW)
        models[PRIMARY_MODEL_NAME].append(
            {
                **row,
                "actual_clicks": int(row["clicks"]),
                "forecast_clicks": forecast_clicks,
                "actual_ctr": float(row["ctr"]),
                "forecast_ctr": forecast_ctr,
                "model_name": PRIMARY_MODEL_NAME,
            }
        )
        rolling_clicks.append(float(row["clicks"]))
        rolling_ctrs.append(float(row["ctr"]))

    last_click = train_clicks[-1]
    last_ctr = train_ctrs[-1]
    for row in holdout_rows:
        models["naive_last_hour"].append(
            {
                **row,
                "actual_clicks": int(row["clicks"]),
                "forecast_clicks": last_click,
                "actual_ctr": float(row["ctr"]),
                "forecast_ctr": last_ctr,
                "model_name": "naive_last_hour",
            }
        )

    model_metrics: dict[str, dict[str, float | None]] = {}
    for model_name, predictions in models.items():
        actual_clicks = [float(item["actual_clicks"]) for item in predictions]
        forecast_clicks = [float(item["forecast_clicks"]) for item in predictions]
        model_metrics[model_name] = _compute_error_metrics(actual_clicks, forecast_clicks)

    best_model = min(
        model_metrics,
        key=lambda name: model_metrics[name]["mae"]
        if model_metrics[name]["mae"] is not None
        else float("inf"),
    )

    return {
        "holdout_hours": holdout_hours,
        "train_hours": len(train_rows),
        "models": models,
        "model_metrics": model_metrics,
        "selected_model": best_model,
        "selected_predictions": models[best_model],
    }


def insert_forecast_results(
    connection: duckdb.DuckDBPyConnection,
    predictions: list[dict[str, Any]],
    metrics: dict[str, float | None],
) -> None:
    for row in predictions:
        connection.execute(
            f"""
            INSERT INTO {RESULTS_TABLE} (
                event_date,
                event_hour,
                actual_clicks,
                forecast_clicks,
                actual_ctr,
                forecast_ctr,
                model_name,
                mae,
                rmse,
                mape
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                row["event_date"],
                row["event_hour"],
                row["actual_clicks"],
                row["forecast_clicks"],
                row["actual_ctr"],
                row["forecast_ctr"],
                row["model_name"],
                metrics.get("mae"),
                metrics.get("rmse"),
                metrics.get("mape"),
            ],
        )


def build_summary(
    config: DatabaseConfig,
    staging_rows: int,
    series: list[dict[str, Any]],
    forecast_payload: dict[str, Any],
    results_count: int,
) -> dict[str, Any]:
    input_impressions = sum(row["impressions"] for row in series)
    selected_metrics = forecast_payload["model_metrics"][forecast_payload["selected_model"]]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database_path": _display_path(config.database_path),
        "source_table": "stg_ad_events",
        "input_mart": INPUTS_TABLE,
        "results_mart": RESULTS_TABLE,
        "staging_row_count": staging_rows,
        "input_row_count": len(series),
        "results_row_count": results_count,
        "holdout_hours": forecast_payload["holdout_hours"],
        "train_hours": forecast_payload["train_hours"],
        "selected_model": forecast_payload["selected_model"],
        "model_metrics": forecast_payload["model_metrics"],
        "selected_metrics": selected_metrics,
        "total_impressions": input_impressions,
        "success": (
            len(series) >= MIN_SERIES_LENGTH
            and results_count > 0
            and input_impressions == staging_rows
            and selected_metrics.get("mae") is not None
        ),
    }


def write_forecast_summary(summary: dict[str, Any], path: Path | None = None) -> Path:
    output_path = path or FORECAST_SUMMARY
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2))
    return output_path


def run_ctr_forecast(
    config: DatabaseConfig | None = None,
    summary_path: Path | None = None,
    holdout_hours: int = DEFAULT_HOLDOUT_HOURS,
) -> dict[str, Any]:
    config = config or load_config()
    ensure_database_ready(config)

    connection = duckdb.connect(str(config.database_path))
    try:
        staging_rows = ensure_staging_has_data(connection)
        clear_mart_tables(connection)
        connection.execute(FORECAST_INPUTS_INSERT_SQL)
        series = fetch_hourly_series(connection)
        forecast_payload = build_model_forecasts(series, holdout_hours=holdout_hours)
        selected_metrics = forecast_payload["model_metrics"][forecast_payload["selected_model"]]
        insert_forecast_results(
            connection,
            forecast_payload["selected_predictions"],
            selected_metrics,
        )
        results_count = int(
            connection.execute(f"SELECT COUNT(*) FROM {RESULTS_TABLE}").fetchone()[0]
        )
    finally:
        connection.close()

    summary = build_summary(
        config=config,
        staging_rows=staging_rows,
        series=series,
        forecast_payload=forecast_payload,
        results_count=results_count,
    )
    write_forecast_summary(summary, summary_path)
    return summary


def main() -> int:
    print("=" * 60)
    print("CTR forecast mart build")
    print("=" * 60)

    try:
        config = load_config()
        summary = run_ctr_forecast(config)

        print(f"Database: {config.database_path}")
        print(f"Source:   stg_ad_events ({summary['staging_row_count']:,} rows)")
        print(
            f"Inputs:   {INPUTS_TABLE} ({summary['input_row_count']:,} hourly rows)"
        )
        print(
            f"Results:  {RESULTS_TABLE} ({summary['results_row_count']:,} holdout rows)"
        )
        print()
        print(f"Selected model: {summary['selected_model']}")
        metrics = summary["selected_metrics"]
        print(
            f"Holdout metrics: MAE={metrics['mae']}, RMSE={metrics['rmse']}, "
            f"MAPE={metrics['mape']}"
        )
        print()
        print(f"Summary written to {FORECAST_SUMMARY}")

        if not summary["success"]:
            print("CTR forecast build did not complete successfully.", file=sys.stderr)
            return 1
        return 0

    except RuntimeError as exc:
        print(f"CTR forecast failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
