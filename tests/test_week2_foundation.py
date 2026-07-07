"""Week 2 analytics foundation and end-to-end integration tests."""

from __future__ import annotations

import json

import duckdb
import pandas as pd
import pytest

import create_duckdb_database as db_setup
import generate_week2_analytics_lock as week2_lock
import validate_data as validator
from clean_avazu_ads import clean_avazu_ads
from clean_hillstrom_email import clean_hillstrom_email
from helpers import (
    PROJECT_ROOT,
    WEEK2_ALL_SCRIPTS,
    WEEK2_LOCKED,
    run_full_week2_pipeline,
    tiny_avazu_dataframe,
    tiny_hillstrom_dataframe,
)
from paths import SQL_DIR, WEEK2_ANALYTICS_LOCK_DOC

pytestmark = [pytest.mark.week2, pytest.mark.integration]


def test_week2_analytics_lock_doc_exists():
    assert WEEK2_ANALYTICS_LOCK_DOC.is_file()


def test_all_week2_scripts_exist():
    for script_name in WEEK2_ALL_SCRIPTS:
        assert (PROJECT_ROOT / "scripts" / script_name).is_file()
    assert (PROJECT_ROOT / "scripts" / "generate_week2_analytics_lock.py").is_file()


@pytest.mark.parametrize(
    "term",
    [
        "Status:** Locked",
        "16.4074%",
        "mart_device_app_performance",
        "generate_week2_analytics_lock.py",
        "Phase 3 boundary",
    ],
)
def test_week2_lock_contains_frozen_stats(term: str):
    assert term in WEEK2_ANALYTICS_LOCK_DOC.read_text(encoding="utf-8")


def test_full_week2_pipeline_populates_marts_and_exports(tmp_path):
    raw_dir = tmp_path / "data" / "raw"
    processed = tmp_path / "data" / "processed"
    marts = tmp_path / "data" / "marts"
    exports = tmp_path / "data" / "exports"
    docs = tmp_path / "docs"
    excel_dir = tmp_path / "excel"
    for directory in (raw_dir, processed, marts, exports, docs, excel_dir):
        directory.mkdir(parents=True)

    avazu_raw = raw_dir / "avazu_train.csv"
    hillstrom_raw = raw_dir / "hillstrom_email.csv"
    tiny_avazu_dataframe().to_csv(avazu_raw, index=False)
    tiny_hillstrom_dataframe().to_csv(hillstrom_raw, index=False)

    avazu_clean, avazu_summary = clean_avazu_ads(pd.read_csv(avazu_raw))
    hillstrom_clean, hillstrom_summary = clean_hillstrom_email(pd.read_csv(hillstrom_raw))
    avazu_parquet = processed / "avazu_clean.parquet"
    hillstrom_parquet = processed / "hillstrom_clean.parquet"
    avazu_clean.to_parquet(avazu_parquet, index=False)
    hillstrom_clean.to_parquet(hillstrom_parquet, index=False)

    config = db_setup.DatabaseConfig(database_path=processed / "marketing_analytics.duckdb")
    db_setup.create_database(config=config, sql_dir=SQL_DIR)

    import load_to_duckdb as loader

    loader.load_data(
        config=config,
        targets=loader.get_load_targets(
            avazu_raw=avazu_raw,
            hillstrom_raw=hillstrom_raw,
            avazu_clean=avazu_parquet,
            hillstrom_clean=hillstrom_parquet,
        ),
        summary_path=processed / "duckdb_load_summary.json",
    )

    run_full_week2_pipeline(
        config,
        processed,
        docs_dir=docs,
        marts_dir=marts,
        exports_dir=exports,
        excel_path=excel_dir / "marketing_executive_workbook.xlsx",
    )

    connection = duckdb.connect(str(config.database_path), read_only=True)
    try:
        for table_name in (
            "mart_campaign_kpis",
            "mart_ctr_trends",
            "mart_device_app_performance",
            "mart_ab_test_results",
            "mart_forecast_inputs",
            "mart_forecast_results",
        ):
            count = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            assert int(count) > 0
    finally:
        connection.close()

    export_summary = json.loads((processed / "export_dashboard_summary.json").read_text())
    assert export_summary["success"] is True
    assert export_summary["export_count"] == 6
    assert (marts / "recommendation_matrix.csv").is_file()
    assert (exports / "tableau_data_manifest.json").is_file()


def test_generate_week2_lock_from_summaries(tmp_path, monkeypatch):
    processed = tmp_path / "processed"
    processed.mkdir()

    summaries = {
        "campaign_kpi_summary.json": {
            "success": True,
            "database_path": "data/processed/marketing_analytics.duckdb",
            "mart_row_count": 1,
            "total_impressions": 500000,
            "total_clicks": 82037,
            "overall_ctr": 0.164074,
        },
        "funnel_segment_summary.json": {
            "success": True,
            "marts": {
                "mart_ctr_trends": {"row_count": 4},
                "mart_device_app_performance": {"row_count": 83},
            },
            "segment_rankings": {
                "top_by_ctr": [
                    {
                        "ctr": 0.25251,
                        "impressions": 68033,
                    }
                ]
            },
        },
        "ab_test_summary.json": {
            "success": True,
            "mart_row_count": 3,
            "significant_treatments": ["mens_email", "womens_email"],
            "results": [
                {
                    "treatment_group": "control",
                    "recipients": 21306,
                    "conversion_rate": 0.106167,
                    "absolute_lift": 0.0,
                    "statistically_significant": False,
                },
                {
                    "treatment_group": "mens_email",
                    "recipients": 21307,
                    "conversion_rate": 0.182757,
                    "absolute_lift": 0.07659,
                    "statistically_significant": True,
                },
                {
                    "treatment_group": "womens_email",
                    "recipients": 21387,
                    "conversion_rate": 0.1514,
                    "absolute_lift": 0.045233,
                    "statistically_significant": True,
                },
            ],
        },
        "forecast_summary.json": {
            "success": True,
            "input_row_count": 4,
            "results_row_count": 1,
            "selected_model": "moving_average_3",
            "holdout_hours": 1,
            "train_hours": 3,
            "selected_metrics": {"mae": 19203.0, "rmse": 19203.0, "mape": 314.442443},
        },
        "recommendations_summary.json": {
            "success": True,
            "recommendation_count": 10,
            "action_counts": {"scale": 6, "pause": 3, "retest": 1},
        },
        "export_dashboard_summary.json": {
            "success": True,
            "export_count": 6,
            "excel_workbook": "excel/marketing_executive_workbook.xlsx",
            "tableau_manifest": "data/exports/tableau_data_manifest.json",
            "csv_exports": [
                {"csv_name": "campaign_kpis.csv", "row_count": 1, "description": "Campaign KPIs"},
                {"csv_name": "recommendation_matrix.csv", "row_count": 10, "description": "Matrix"},
            ],
        },
        "data_validation_summary.json": {
            "success": True,
            "passed_count": 25,
            "failed_count": 0,
            "checks": [{"check_name": "mart_campaign_kpis_populated", "status": "pass"}],
        },
    }

    for filename, payload in summaries.items():
        (processed / filename).write_text(json.dumps(payload), encoding="utf-8")

    monkeypatch.setattr(week2_lock, "CAMPAIGN_KPI_SUMMARY", processed / "campaign_kpi_summary.json")
    monkeypatch.setattr(week2_lock, "FUNNEL_SEGMENT_SUMMARY", processed / "funnel_segment_summary.json")
    monkeypatch.setattr(week2_lock, "AB_TEST_SUMMARY", processed / "ab_test_summary.json")
    monkeypatch.setattr(week2_lock, "FORECAST_SUMMARY", processed / "forecast_summary.json")
    monkeypatch.setattr(week2_lock, "RECOMMENDATIONS_SUMMARY", processed / "recommendations_summary.json")
    monkeypatch.setattr(week2_lock, "EXPORT_DASHBOARD_SUMMARY", processed / "export_dashboard_summary.json")
    monkeypatch.setattr(week2_lock, "DATA_VALIDATION_SUMMARY", processed / "data_validation_summary.json")

    output = tmp_path / "week2_analytics_lock.md"
    week2_lock.generate_week2_analytics_lock(output_path=output)
    content = output.read_text(encoding="utf-8")
    assert "Status:** Locked" in content
    assert f"scale={WEEK2_LOCKED['recommendation_scale']}" in content


def test_week2_pipeline_validation_passes_after_full_run(tmp_path):
    raw_dir = tmp_path / "data" / "raw"
    processed = tmp_path / "data" / "processed"
    marts = tmp_path / "data" / "marts"
    exports = tmp_path / "data" / "exports"
    docs = tmp_path / "docs"
    excel_dir = tmp_path / "excel"
    for directory in (raw_dir, processed, marts, exports, docs, excel_dir):
        directory.mkdir(parents=True)

    avazu_raw = raw_dir / "avazu_train.csv"
    hillstrom_raw = raw_dir / "hillstrom_email.csv"
    tiny_avazu_dataframe().to_csv(avazu_raw, index=False)
    tiny_hillstrom_dataframe().to_csv(hillstrom_raw, index=False)

    avazu_clean, avazu_summary = clean_avazu_ads(pd.read_csv(avazu_raw))
    hillstrom_clean, hillstrom_summary = clean_hillstrom_email(pd.read_csv(hillstrom_raw))
    avazu_parquet = processed / "avazu_clean.parquet"
    hillstrom_parquet = processed / "hillstrom_clean.parquet"
    avazu_clean.to_parquet(avazu_parquet, index=False)
    hillstrom_clean.to_parquet(hillstrom_parquet, index=False)

    config = db_setup.DatabaseConfig(database_path=processed / "marketing_analytics.duckdb")
    db_setup.create_database(config=config, sql_dir=SQL_DIR)

    import load_to_duckdb as loader

    loader.load_data(
        config=config,
        targets=loader.get_load_targets(
            avazu_raw=avazu_raw,
            hillstrom_raw=hillstrom_raw,
            avazu_clean=avazu_parquet,
            hillstrom_clean=hillstrom_parquet,
        ),
        summary_path=processed / "duckdb_load_summary.json",
    )

    run_full_week2_pipeline(
        config,
        processed,
        docs_dir=docs,
        marts_dir=marts,
        exports_dir=exports,
        excel_path=excel_dir / "marketing_executive_workbook.xlsx",
    )

    expectations = {
        "profile": {
            "avazu": {"row_count": len(avazu_clean)},
            "hillstrom": {"row_count": len(hillstrom_clean)},
        },
        "cleaning": {
            "avazu": {
                "input_rows": len(avazu_clean),
                "output_rows": len(avazu_clean),
                "ctr": avazu_summary["ctr"],
            },
            "hillstrom": {
                "input_rows": len(hillstrom_clean),
                "output_rows": len(hillstrom_clean),
                "visit_rate": hillstrom_summary["visit_rate"],
                "treatment_group_counts": hillstrom_summary["treatment_group_counts"],
            },
        },
    }
    validation = validator.run_validation(
        config=config,
        expectations=expectations,
        summary_path=processed / "data_validation_summary.json",
    )

    check_status = {check["check_name"]: check["status"] for check in validation["checks"]}
    for check_name in (
        "mart_campaign_kpis_populated",
        "mart_ctr_trends_populated",
        "mart_device_app_performance_populated",
        "mart_ab_test_results_populated",
        "mart_forecast_results_populated",
    ):
        assert check_status[check_name] == "pass", check_name
