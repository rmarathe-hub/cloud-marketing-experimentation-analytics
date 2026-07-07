"""run_funnel_segment_analysis.py tests for Day 9 funnel and segment marts."""

from __future__ import annotations

import json

import duckdb
import pandas as pd
import pytest

import create_duckdb_database as db_setup
import load_to_duckdb as loader
import run_campaign_kpis as campaign_kpis
import run_funnel_segment_analysis as funnel_segment
import validate_data as validator
from clean_avazu_ads import clean_avazu_ads
from helpers import (
    DUCKDB_MART_TABLES_PENDING,
    DUCKDB_MART_TABLES_POPULATED,
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


def test_funnel_segment_module_exports_main():
    assert hasattr(funnel_segment, "main")
    assert hasattr(funnel_segment, "run_funnel_segment_analysis")


def test_run_funnel_segment_analysis_populates_marts(tmp_path):
    bundle = _build_tiny_avazu_bundle(tmp_path)
    summary_path = bundle["processed"] / "funnel_segment_summary.json"

    summary = funnel_segment.run_funnel_segment_analysis(
        config=bundle["config"],
        summary_path=summary_path,
        min_impressions_for_ranking=1,
    )

    assert summary["success"] is True
    assert summary["marts"]["mart_ctr_trends"]["row_count"] >= 1
    assert summary["marts"]["mart_device_app_performance"]["row_count"] >= 1
    assert summary_path.exists()

    connection = duckdb.connect(str(bundle["config"].database_path), read_only=True)
    try:
        for table_name in ("mart_ctr_trends", "mart_device_app_performance"):
            assert table_name in DUCKDB_MART_TABLES_POPULATED
            count = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            assert count > 0
        for table_name in DUCKDB_MART_TABLES_PENDING:
            pending_count = connection.execute(
                f"SELECT COUNT(*) FROM {table_name}"
            ).fetchone()[0]
            assert pending_count == 0
    finally:
        connection.close()


def test_hourly_trends_reconcile_with_staging(tmp_path):
    bundle = _build_tiny_avazu_bundle(tmp_path)
    summary = funnel_segment.run_funnel_segment_analysis(
        config=bundle["config"],
        summary_path=bundle["processed"] / "funnel_segment_summary.json",
        min_impressions_for_ranking=1,
    )

    ctr_summary = summary["marts"]["mart_ctr_trends"]
    assert ctr_summary["total_impressions"] == bundle["staging_rows"]
    assert ctr_summary["total_clicks"] <= bundle["staging_rows"]


def test_segment_click_share_sums_to_one(tmp_path):
    bundle = _build_tiny_avazu_bundle(tmp_path)
    funnel_segment.run_funnel_segment_analysis(
        config=bundle["config"],
        summary_path=bundle["processed"] / "funnel_segment_summary.json",
        min_impressions_for_ranking=1,
    )

    connection = duckdb.connect(str(bundle["config"].database_path), read_only=True)
    try:
        click_share_sum = connection.execute(
            "SELECT SUM(click_share) FROM mart_device_app_performance"
        ).fetchone()[0]
    finally:
        connection.close()

    assert_approx_ratio(float(click_share_sum), 1.0)


def test_run_funnel_segment_analysis_is_idempotent(tmp_path):
    bundle = _build_tiny_avazu_bundle(tmp_path)
    summary_path = bundle["processed"] / "funnel_segment_summary.json"

    first = funnel_segment.run_funnel_segment_analysis(
        config=bundle["config"],
        summary_path=summary_path,
        min_impressions_for_ranking=1,
    )
    second = funnel_segment.run_funnel_segment_analysis(
        config=bundle["config"],
        summary_path=summary_path,
        min_impressions_for_ranking=1,
    )

    assert (
        first["marts"]["mart_ctr_trends"]["row_count"]
        == second["marts"]["mart_ctr_trends"]["row_count"]
    )
    assert (
        first["marts"]["mart_device_app_performance"]["row_count"]
        == second["marts"]["mart_device_app_performance"]["row_count"]
    )


def test_funnel_segment_summary_schema(tmp_path):
    bundle = _build_tiny_avazu_bundle(tmp_path)
    summary_path = bundle["processed"] / "funnel_segment_summary.json"
    funnel_segment.run_funnel_segment_analysis(
        config=bundle["config"],
        summary_path=summary_path,
        min_impressions_for_ranking=1,
    )

    payload = json.loads(summary_path.read_text())
    for key in [
        "generated_at",
        "staging_row_count",
        "marts",
        "segment_rankings",
        "success",
    ]:
        assert key in payload
    assert "top_by_ctr" in payload["segment_rankings"]
    assert "bottom_by_ctr" in payload["segment_rankings"]


def test_validation_passes_after_funnel_segment_marts(tmp_path):
    bundle = _build_tiny_avazu_bundle(tmp_path)
    processed = bundle["processed"]
    campaign_kpis.run_campaign_kpis(
        config=bundle["config"],
        summary_path=processed / "campaign_kpi_summary.json",
    )
    funnel_segment.run_funnel_segment_analysis(
        config=bundle["config"],
        summary_path=processed / "funnel_segment_summary.json",
        min_impressions_for_ranking=1,
    )

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

    funnel_checks = {
        check["check_name"]: check
        for check in validation_summary["checks"]
        if check["check_name"].startswith("mart_ctr_trends")
        or check["check_name"].startswith("mart_device_app_performance")
    }
    assert funnel_checks["mart_ctr_trends_populated"]["status"] == "pass"
    assert funnel_checks["mart_device_app_performance_populated"]["status"] == "pass"
    assert funnel_checks["mart_device_app_performance_click_share"]["status"] == "pass"


@pytest.mark.data
@pytest.mark.slow
def test_real_funnel_segment_marts_reconcile():
    from helpers import local_duckdb_available

    if not local_duckdb_available():
        pytest.skip("Local DuckDB database not present")

    from paths import DUCKDB_DEFAULT_PATH

    connection = duckdb.connect(str(DUCKDB_DEFAULT_PATH), read_only=True)
    try:
        ctr_count = connection.execute("SELECT COUNT(*) FROM mart_ctr_trends").fetchone()[0]
        device_count = connection.execute(
            "SELECT COUNT(*) FROM mart_device_app_performance"
        ).fetchone()[0]
        if ctr_count == 0 or device_count == 0:
            pytest.skip("Funnel/segment marts not populated; run run_funnel_segment_analysis.py")

        ctr_impressions = connection.execute(
            "SELECT SUM(impressions) FROM mart_ctr_trends"
        ).fetchone()[0]
        device_impressions = connection.execute(
            "SELECT SUM(impressions) FROM mart_device_app_performance"
        ).fetchone()[0]
        click_share_sum = connection.execute(
            "SELECT SUM(click_share) FROM mart_device_app_performance"
        ).fetchone()[0]
    finally:
        connection.close()

    assert ctr_impressions == WEEK1_LOCKED["avazu_rows"]
    assert device_impressions == WEEK1_LOCKED["avazu_rows"]
    assert_approx_ratio(float(click_share_sum), 1.0)


def test_run_implemented_week2_analytics_helper(tmp_path):
    bundle = _build_tiny_avazu_bundle(tmp_path)
    run_implemented_week2_analytics(bundle["config"], bundle["processed"])

    connection = duckdb.connect(str(bundle["config"].database_path), read_only=True)
    try:
        for table_name in (
            "mart_campaign_kpis",
            "mart_ctr_trends",
            "mart_device_app_performance",
            "mart_forecast_inputs",
            "mart_forecast_results",
        ):
            count = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            assert count > 0
        ab_count = connection.execute(
            "SELECT COUNT(*) FROM mart_ab_test_results"
        ).fetchone()[0]
        assert ab_count == 0
    finally:
        connection.close()
