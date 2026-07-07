"""Week 2 reproducibility and idempotency tests."""

from __future__ import annotations

import json

import duckdb
import pandas as pd
import pytest

import create_duckdb_database as db_setup
import export_dashboard_data as dashboard_exports
import generate_recommendations as recommendations
import load_to_duckdb as loader
import run_ab_test_analysis as ab_test
import run_campaign_kpis as campaign_kpis
import run_ctr_forecast as ctr_forecast
import run_funnel_segment_analysis as funnel_segment
from clean_avazu_ads import clean_avazu_ads
from clean_hillstrom_email import clean_hillstrom_email
from helpers import tiny_avazu_dataframe, tiny_hillstrom_dataframe
from paths import SQL_DIR

pytestmark = [pytest.mark.smoke, pytest.mark.week2, pytest.mark.integration]


def _build_bundle(tmp_path):
    raw_dir = tmp_path / "raw"
    processed = tmp_path / "processed"
    docs = tmp_path / "docs"
    marts = tmp_path / "marts"
    exports = tmp_path / "exports"
    excel_dir = tmp_path / "excel"
    for directory in (raw_dir, processed, docs, marts, exports, excel_dir):
        directory.mkdir(parents=True)

    avazu_raw = raw_dir / "avazu_train.csv"
    hillstrom_raw = raw_dir / "hillstrom_email.csv"
    tiny_avazu_dataframe().to_csv(avazu_raw, index=False)
    tiny_hillstrom_dataframe().to_csv(hillstrom_raw, index=False)

    avazu_clean, _ = clean_avazu_ads(pd.read_csv(avazu_raw))
    hillstrom_clean, _ = clean_hillstrom_email(pd.read_csv(hillstrom_raw))
    avazu_parquet = processed / "avazu_clean.parquet"
    hillstrom_parquet = processed / "hillstrom_clean.parquet"
    avazu_clean.to_parquet(avazu_parquet, index=False)
    hillstrom_clean.to_parquet(hillstrom_parquet, index=False)

    config = db_setup.DatabaseConfig(database_path=processed / "marketing_analytics.duckdb")
    db_setup.create_database(config=config, sql_dir=SQL_DIR)
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
    return {
        "config": config,
        "processed": processed,
        "docs": docs,
        "marts": marts,
        "exports": exports,
        "excel_path": excel_dir / "marketing_executive_workbook.xlsx",
    }


@pytest.mark.parametrize(
    "runner,summary_name",
    [
        (campaign_kpis.run_campaign_kpis, "campaign_kpi_summary.json"),
        (funnel_segment.run_funnel_segment_analysis, "funnel_segment_summary.json"),
        (ab_test.run_ab_test_analysis, "ab_test_summary.json"),
        (ctr_forecast.run_ctr_forecast, "forecast_summary.json"),
    ],
)
def test_week2_mart_scripts_are_idempotent(tmp_path, runner, summary_name: str):
    bundle = _build_bundle(tmp_path)
    kwargs = {"config": bundle["config"], "summary_path": bundle["processed"] / summary_name}
    if runner is funnel_segment.run_funnel_segment_analysis:
        kwargs["min_impressions_for_ranking"] = 1
    first = runner(**kwargs)
    second = runner(**kwargs)
    assert first["success"] is True
    assert second["success"] is True


def test_recommendations_generation_is_idempotent(tmp_path):
    bundle = _build_bundle(tmp_path)
    campaign_kpis.run_campaign_kpis(
        config=bundle["config"],
        summary_path=bundle["processed"] / "campaign_kpi_summary.json",
    )
    funnel_segment.run_funnel_segment_analysis(
        config=bundle["config"],
        summary_path=bundle["processed"] / "funnel_segment_summary.json",
        min_impressions_for_ranking=1,
    )
    ab_test.run_ab_test_analysis(
        config=bundle["config"],
        summary_path=bundle["processed"] / "ab_test_summary.json",
    )
    ctr_forecast.run_ctr_forecast(
        config=bundle["config"],
        summary_path=bundle["processed"] / "forecast_summary.json",
    )

    kwargs = {
        "config": bundle["config"],
        "recommendations_path": bundle["docs"] / "recommendations.md",
        "executive_path": bundle["docs"] / "executive_summary.md",
        "summary_path": bundle["processed"] / "recommendations_summary.json",
    }
    first = recommendations.generate_recommendations(**kwargs)
    second = recommendations.generate_recommendations(**kwargs)
    assert first["recommendation_count"] == second["recommendation_count"]


def test_export_dashboard_data_is_idempotent(tmp_path):
    bundle = _build_bundle(tmp_path)
    campaign_kpis.run_campaign_kpis(
        config=bundle["config"],
        summary_path=bundle["processed"] / "campaign_kpi_summary.json",
    )
    funnel_segment.run_funnel_segment_analysis(
        config=bundle["config"],
        summary_path=bundle["processed"] / "funnel_segment_summary.json",
        min_impressions_for_ranking=1,
    )
    ab_test.run_ab_test_analysis(
        config=bundle["config"],
        summary_path=bundle["processed"] / "ab_test_summary.json",
    )
    ctr_forecast.run_ctr_forecast(
        config=bundle["config"],
        summary_path=bundle["processed"] / "forecast_summary.json",
    )
    recommendations.generate_recommendations(
        config=bundle["config"],
        recommendations_path=bundle["docs"] / "recommendations.md",
        executive_path=bundle["docs"] / "executive_summary.md",
        summary_path=bundle["processed"] / "recommendations_summary.json",
    )

    kwargs = {
        "config": bundle["config"],
        "marts_dir": bundle["marts"],
        "exports_dir": bundle["exports"],
        "excel_path": bundle["excel_path"],
        "recommendations_summary_path": bundle["processed"] / "recommendations_summary.json",
        "summary_path": bundle["processed"] / "export_dashboard_summary.json",
    }
    first = dashboard_exports.export_dashboard_data(**kwargs)
    second = dashboard_exports.export_dashboard_data(**kwargs)
    assert first["export_count"] == second["export_count"]

    connection = duckdb.connect(str(bundle["config"].database_path), read_only=True)
    try:
        campaign_rows = connection.execute("SELECT COUNT(*) FROM mart_campaign_kpis").fetchone()[0]
    finally:
        connection.close()
    assert int(campaign_rows) >= 1
