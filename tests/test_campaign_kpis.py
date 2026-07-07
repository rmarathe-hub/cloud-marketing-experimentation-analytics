"""run_campaign_kpis.py tests for Day 8 campaign KPI mart."""

from __future__ import annotations

import json

import duckdb
import pandas as pd
import pytest

import create_duckdb_database as db_setup
import load_to_duckdb as loader
import run_campaign_kpis as campaign_kpis
import validate_data as validator
from clean_avazu_ads import clean_avazu_ads
from helpers import (
    DUCKDB_MART_TABLES_PENDING,
    DUCKDB_MART_TABLES_POPULATED,
    WEEK1_LOCKED,
    assert_approx_ratio,
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


def test_campaign_kpi_module_exports_main():
    assert hasattr(campaign_kpis, "main")
    assert hasattr(campaign_kpis, "run_campaign_kpis")


def test_run_campaign_kpis_populates_mart(tmp_path):
    bundle = _build_tiny_avazu_bundle(tmp_path)
    summary_path = bundle["processed"] / "campaign_kpi_summary.json"

    summary = campaign_kpis.run_campaign_kpis(
        config=bundle["config"],
        summary_path=summary_path,
    )

    assert summary["success"] is True
    assert summary["mart_row_count"] >= 1
    assert summary["total_impressions"] == bundle["staging_rows"]
    assert summary_path.exists()

    connection = duckdb.connect(str(bundle["config"].database_path), read_only=True)
    try:
        mart_count = connection.execute(
            "SELECT COUNT(*) FROM mart_campaign_kpis"
        ).fetchone()[0]
        assert mart_count == summary["mart_row_count"]
        for table_name in DUCKDB_MART_TABLES_PENDING:
            pending_count = connection.execute(
                f"SELECT COUNT(*) FROM {table_name}"
            ).fetchone()[0]
            assert pending_count == 0
    finally:
        connection.close()


def test_run_campaign_kpis_ctr_matches_staging(tmp_path):
    bundle = _build_tiny_avazu_bundle(tmp_path)
    summary = campaign_kpis.run_campaign_kpis(
        config=bundle["config"],
        summary_path=bundle["processed"] / "campaign_kpi_summary.json",
    )

    connection = duckdb.connect(str(bundle["config"].database_path), read_only=True)
    try:
        staging_ctr = connection.execute(
            "SELECT AVG(CAST(click AS DOUBLE)) FROM stg_ad_events"
        ).fetchone()[0]
        mart_ctr = connection.execute(
            """
            SELECT CASE
                WHEN SUM(impressions) = 0 THEN 0.0
                ELSE SUM(clicks)::DOUBLE / SUM(impressions)::DOUBLE
            END
            FROM mart_campaign_kpis
            """
        ).fetchone()[0]
    finally:
        connection.close()

    assert_approx_ratio(summary["overall_ctr"], float(staging_ctr))
    assert_approx_ratio(float(mart_ctr), float(staging_ctr))


def test_run_campaign_kpis_is_idempotent(tmp_path):
    bundle = _build_tiny_avazu_bundle(tmp_path)
    summary_path = bundle["processed"] / "campaign_kpi_summary.json"

    first = campaign_kpis.run_campaign_kpis(
        config=bundle["config"],
        summary_path=summary_path,
    )
    second = campaign_kpis.run_campaign_kpis(
        config=bundle["config"],
        summary_path=summary_path,
    )

    assert first["mart_row_count"] == second["mart_row_count"]
    assert first["daily_kpis"] == second["daily_kpis"]


def test_run_campaign_kpis_summary_schema(tmp_path):
    bundle = _build_tiny_avazu_bundle(tmp_path)
    summary_path = bundle["processed"] / "campaign_kpi_summary.json"
    campaign_kpis.run_campaign_kpis(config=bundle["config"], summary_path=summary_path)

    payload = json.loads(summary_path.read_text())
    for key in [
        "generated_at",
        "mart_table",
        "mart_row_count",
        "total_impressions",
        "total_clicks",
        "overall_ctr",
        "daily_kpis",
        "success",
    ]:
        assert key in payload
    assert payload["mart_table"] == "mart_campaign_kpis"
    assert isinstance(payload["daily_kpis"], list)


def test_validation_passes_after_campaign_kpis(tmp_path):
    bundle = _build_tiny_avazu_bundle(tmp_path)
    processed = bundle["processed"]
    campaign_kpis.run_campaign_kpis(
        config=bundle["config"],
        summary_path=processed / "campaign_kpi_summary.json",
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

    campaign_checks = {
        check["check_name"]: check
        for check in validation_summary["checks"]
        if check["check_name"].startswith("mart_campaign_kpis")
    }
    assert campaign_checks["mart_campaign_kpis_populated"]["status"] == "pass"
    assert campaign_checks["mart_campaign_kpis_ctr"]["status"] == "pass"


@pytest.mark.data
@pytest.mark.slow
def test_real_campaign_kpi_mart_matches_lock():
    from helpers import local_duckdb_available

    if not local_duckdb_available():
        pytest.skip("Local DuckDB database not present")

    from paths import DUCKDB_DEFAULT_PATH

    connection = duckdb.connect(str(DUCKDB_DEFAULT_PATH), read_only=True)
    try:
        mart_count = connection.execute(
            "SELECT COUNT(*) FROM mart_campaign_kpis"
        ).fetchone()[0]
        if mart_count == 0:
            pytest.skip("mart_campaign_kpis not populated; run run_campaign_kpis.py")

        impressions, clicks = connection.execute(
            "SELECT SUM(impressions), SUM(clicks) FROM mart_campaign_kpis"
        ).fetchone()
        ctr = connection.execute(
            """
            SELECT CASE
                WHEN SUM(impressions) = 0 THEN 0.0
                ELSE SUM(clicks)::DOUBLE / SUM(impressions)::DOUBLE
            END
            FROM mart_campaign_kpis
            """
        ).fetchone()[0]
    finally:
        connection.close()

    assert impressions == WEEK1_LOCKED["avazu_rows"]
    assert clicks == WEEK1_LOCKED["avazu_clicks"]
    assert_approx_ratio(float(ctr), WEEK1_LOCKED["avazu_ctr_ratio"])


def test_populated_mart_tables_constant():
    assert DUCKDB_MART_TABLES_POPULATED == ("mart_campaign_kpis",)
