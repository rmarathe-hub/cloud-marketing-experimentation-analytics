"""run_ctr_forecast.py tests for Day 11 CTR forecasting marts."""

from __future__ import annotations

import json

import duckdb
import pandas as pd
import pytest

import create_duckdb_database as db_setup
import load_to_duckdb as loader
import run_ctr_forecast as ctr_forecast
import validate_data as validator
from clean_avazu_ads import clean_avazu_ads
from helpers import (
    DUCKDB_MART_TABLES,
    WEEK1_LOCKED,
    assert_approx_ratio,
    run_implemented_week2_analytics,
    tiny_avazu_dataframe,
    write_tiny_avazu_csv,
)
from paths import SQL_DIR

pytestmark = [pytest.mark.unit, pytest.mark.duckdb]


def _build_tiny_avazu_bundle(tmp_path):
    raw_dir = tmp_path / "raw"
    processed = tmp_path / "processed"
    raw_dir.mkdir(parents=True)
    processed.mkdir(parents=True)

    avazu_raw = write_tiny_avazu_csv(raw_dir / "avazu_train.csv")
    avazu_df = pd.read_csv(avazu_raw)
    avazu_clean, avazu_summary = clean_avazu_ads(avazu_df)
    avazu_parquet = processed / "avazu_clean.parquet"
    avazu_clean.to_parquet(avazu_parquet, index=False)

    db_path = processed / "marketing_analytics.duckdb"
    config = db_setup.DatabaseConfig(database_path=db_path)
    db_setup.create_database(config=config, sql_dir=SQL_DIR)

    loader.load_data(
        config=config,
        targets=[
            loader.LoadTarget("stg_ad_events", "staging", avazu_parquet, "parquet"),
        ],
        summary_path=processed / "duckdb_load_summary.json",
    )
    return {
        "config": config,
        "processed": processed,
        "avazu_summary": avazu_summary,
        "staging_rows": len(avazu_clean),
    }


def test_ctr_forecast_module_exports_main():
    assert hasattr(ctr_forecast, "main")
    assert hasattr(ctr_forecast, "run_ctr_forecast")


def test_run_ctr_forecast_populates_marts(tmp_path):
    bundle = _build_tiny_avazu_bundle(tmp_path)
    summary_path = bundle["processed"] / "forecast_summary.json"

    summary = ctr_forecast.run_ctr_forecast(
        config=bundle["config"],
        summary_path=summary_path,
    )

    assert summary["success"] is True
    assert summary["input_row_count"] >= ctr_forecast.MIN_SERIES_LENGTH
    assert summary["results_row_count"] >= 1
    assert summary_path.exists()

    connection = duckdb.connect(str(bundle["config"].database_path), read_only=True)
    try:
        for table_name in ("mart_forecast_inputs", "mart_forecast_results"):
            count = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            assert count > 0
    finally:
        connection.close()


def test_forecast_inputs_reconcile_with_staging(tmp_path):
    bundle = _build_tiny_avazu_bundle(tmp_path)
    summary = ctr_forecast.run_ctr_forecast(
        config=bundle["config"],
        summary_path=bundle["processed"] / "forecast_summary.json",
    )

    assert summary["total_impressions"] == bundle["staging_rows"]
    assert summary["selected_metrics"]["mae"] is not None
    assert summary["selected_metrics"]["rmse"] is not None


def test_compute_error_metrics_handles_zero_actual():
    metrics = ctr_forecast._compute_error_metrics([0.0, 10.0], [1.0, 8.0])
    assert metrics["mae"] == 1.5
    assert metrics["rmse"] is not None
    assert metrics["mape"] == 20.0


def test_run_ctr_forecast_is_idempotent(tmp_path):
    bundle = _build_tiny_avazu_bundle(tmp_path)
    summary_path = bundle["processed"] / "forecast_summary.json"

    first = ctr_forecast.run_ctr_forecast(config=bundle["config"], summary_path=summary_path)
    second = ctr_forecast.run_ctr_forecast(config=bundle["config"], summary_path=summary_path)

    assert first["selected_model"] == second["selected_model"]
    assert first["results_row_count"] == second["results_row_count"]


def test_forecast_summary_schema(tmp_path):
    bundle = _build_tiny_avazu_bundle(tmp_path)
    summary_path = bundle["processed"] / "forecast_summary.json"
    ctr_forecast.run_ctr_forecast(config=bundle["config"], summary_path=summary_path)

    payload = json.loads(summary_path.read_text())
    for key in [
        "generated_at",
        "input_row_count",
        "results_row_count",
        "selected_model",
        "selected_metrics",
        "model_metrics",
        "success",
    ]:
        assert key in payload


def test_validation_passes_after_forecast_marts(tmp_path):
    bundle = _build_tiny_avazu_bundle(tmp_path)
    processed = bundle["processed"]
    run_implemented_week2_analytics(bundle["config"], processed)

    expectations = {
        "profile": {"avazu": {"row_count": bundle["staging_rows"]}, "hillstrom": {"row_count": 0}},
        "cleaning": {
            "avazu": {
                "input_rows": bundle["staging_rows"],
                "output_rows": bundle["staging_rows"],
                "ctr": bundle["avazu_summary"]["ctr"],
            },
            "hillstrom": {
                "input_rows": 0,
                "output_rows": 0,
                "visit_rate": 0.0,
                "treatment_group_counts": {},
            },
        },
    }
    validation_summary = validator.run_validation(
        config=bundle["config"],
        expectations=expectations,
        summary_path=processed / "data_validation_summary.json",
    )

    forecast_checks = {
        check["check_name"]: check
        for check in validation_summary["checks"]
        if check["check_name"].startswith("mart_forecast_")
    }
    assert forecast_checks["mart_forecast_inputs_populated"]["status"] == "pass"
    assert forecast_checks["mart_forecast_results_populated"]["status"] == "pass"
    assert forecast_checks["mart_forecast_results_metrics"]["status"] == "pass"


@pytest.mark.data
@pytest.mark.slow
def test_real_forecast_marts_reconcile():
    from helpers import local_duckdb_available

    if not local_duckdb_available():
        pytest.skip("Local DuckDB database not present")

    from paths import DUCKDB_DEFAULT_PATH

    connection = duckdb.connect(str(DUCKDB_DEFAULT_PATH), read_only=True)
    try:
        input_count = connection.execute(
            "SELECT COUNT(*) FROM mart_forecast_inputs"
        ).fetchone()[0]
        result_count = connection.execute(
            "SELECT COUNT(*) FROM mart_forecast_results"
        ).fetchone()[0]
        if input_count == 0 or result_count == 0:
            pytest.skip("Forecast marts not populated; run run_ctr_forecast.py")

        impressions = connection.execute(
            "SELECT SUM(impressions) FROM mart_forecast_inputs"
        ).fetchone()[0]
        ctr = connection.execute(
            """
            SELECT CASE
                WHEN SUM(impressions) = 0 THEN 0.0
                ELSE SUM(clicks)::DOUBLE / SUM(impressions)::DOUBLE
            END
            FROM mart_forecast_inputs
            """
        ).fetchone()[0]
    finally:
        connection.close()

    assert impressions == WEEK1_LOCKED["avazu_rows"]
    assert_approx_ratio(float(ctr), WEEK1_LOCKED["avazu_ctr_ratio"])


def test_all_mart_tables_are_populated_constants():
    assert len(DUCKDB_MART_TABLES) == 6


def test_forecast_methodology_doc_exists():
    from helpers import DOCS_DIR

    assert (DOCS_DIR / "forecast_methodology.md").is_file()
