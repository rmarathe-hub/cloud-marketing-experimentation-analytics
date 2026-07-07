"""Production data contract tests for Week 2 marts and exports."""

from __future__ import annotations

import json

import duckdb
import pandas as pd
import pytest

from helpers import (
    WEEK1_LOCKED,
    WEEK2_LOCKED,
    assert_approx_ratio,
    assert_csv_contract,
    assert_excel_workbook_contract,
    local_duckdb_available,
    production_exports_available,
    production_marts_populated,
    production_validation_summary_available,
)
from paths import (
    DUCKDB_DEFAULT_PATH,
    EXCEL_WORKBOOK,
    EXPORT_DASHBOARD_SUMMARY,
    EXPORTS_DIR,
    MARTS_DIR,
    RECOMMENDATIONS_SUMMARY,
)

pytestmark = [pytest.mark.data, pytest.mark.slow, pytest.mark.week2]


@pytest.fixture
def duckdb_connection():
    if not local_duckdb_available():
        pytest.skip("Local DuckDB database not present")
    connection = duckdb.connect(str(DUCKDB_DEFAULT_PATH), read_only=True)
    yield connection
    connection.close()


@pytest.mark.parametrize(
    "table_name,expected_rows",
    [
        ("mart_campaign_kpis", WEEK2_LOCKED["campaign_kpi_rows"]),
        ("mart_ctr_trends", WEEK2_LOCKED["ctr_trend_rows"]),
        ("mart_device_app_performance", WEEK2_LOCKED["segment_performance_rows"]),
        ("mart_ab_test_results", WEEK2_LOCKED["ab_test_result_rows"]),
        ("mart_forecast_inputs", WEEK2_LOCKED["forecast_input_rows"]),
        ("mart_forecast_results", WEEK2_LOCKED["forecast_result_rows"]),
    ],
)
def test_production_mart_row_counts(duckdb_connection, table_name: str, expected_rows: int):
    if not production_marts_populated():
        pytest.skip("Production marts not populated")
    count = duckdb_connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    assert int(count) == expected_rows


def test_production_campaign_kpi_metrics(duckdb_connection):
    if not production_marts_populated():
        pytest.skip("Production marts not populated")
    impressions, clicks, ctr = duckdb_connection.execute(
        """
        SELECT SUM(impressions), SUM(clicks),
               CASE WHEN SUM(impressions)=0 THEN 0.0
                    ELSE SUM(clicks)::DOUBLE/SUM(impressions)::DOUBLE END
        FROM mart_campaign_kpis
        """
    ).fetchone()
    assert int(impressions) == WEEK1_LOCKED["avazu_rows"]
    assert int(clicks) == WEEK1_LOCKED["avazu_clicks"]
    assert_approx_ratio(float(ctr), WEEK2_LOCKED["overall_ctr_ratio"])


def test_production_top_segment_matches_lock(duckdb_connection):
    if not production_marts_populated():
        pytest.skip("Production marts not populated")
    row = duckdb_connection.execute(
        """
        SELECT device_type, app_category, site_category, banner_pos,
               impressions, ctr, click_share
        FROM mart_device_app_performance
        WHERE device_type = 1
          AND app_category = '07d7df22'
          AND site_category = 'f028772b'
          AND banner_pos = 1
        """
    ).fetchone()
    assert row is not None
    assert int(row[4]) == WEEK2_LOCKED["top_segment_impressions"]
    assert_approx_ratio(float(row[5]), WEEK2_LOCKED["top_segment_ctr_ratio"], 0.0001)
    assert_approx_ratio(float(row[6]), 0.209406, 0.001)


def test_production_ab_test_lift_and_significance(duckdb_connection):
    if not production_marts_populated():
        pytest.skip("Production marts not populated")
    frame = duckdb_connection.execute(
        "SELECT treatment_group, recipients, conversion_rate, absolute_lift, "
        "incremental_revenue, p_value, statistically_significant "
        "FROM mart_ab_test_results ORDER BY treatment_group"
    ).fetchdf()
    mens = frame[frame["treatment_group"] == "mens_email"].iloc[0]
    womens = frame[frame["treatment_group"] == "womens_email"].iloc[0]
    assert int(mens["recipients"]) == WEEK1_LOCKED["mens_email_recipients"]
    assert int(womens["recipients"]) == WEEK1_LOCKED["womens_email_recipients"]
    assert_approx_ratio(float(mens["absolute_lift"]), WEEK2_LOCKED["mens_email_absolute_lift"])
    assert_approx_ratio(float(womens["absolute_lift"]), WEEK2_LOCKED["womens_email_absolute_lift"])
    assert bool(mens["statistically_significant"]) is True
    assert bool(womens["statistically_significant"]) is True
    assert float(mens["incremental_revenue"]) == pytest.approx(16402.71, rel=0.01)
    assert float(womens["incremental_revenue"]) == pytest.approx(9076.9, rel=0.01)


def test_production_forecast_model_and_mape(duckdb_connection):
    if not production_marts_populated():
        pytest.skip("Production marts not populated")
    row = duckdb_connection.execute(
        "SELECT model_name, mae, rmse, mape FROM mart_forecast_results LIMIT 1"
    ).fetchone()
    assert row[0] == WEEK2_LOCKED["forecast_model"]
    assert float(row[1]) >= 0
    assert float(row[2]) >= 0
    assert_approx_ratio(float(row[3]), WEEK2_LOCKED["forecast_mape"], 0.01)


@pytest.mark.exports
@pytest.mark.parametrize(
    "csv_name,lock_key",
    [
        ("campaign_kpis.csv", "campaign_kpi_rows"),
        ("ctr_trends.csv", "ctr_trend_rows"),
        ("segment_performance.csv", "segment_performance_rows"),
        ("ab_test_results.csv", "ab_test_result_rows"),
        ("forecast_results.csv", "forecast_result_rows"),
        ("recommendation_matrix.csv", "recommendation_count"),
    ],
)
def test_production_mart_csv_row_counts(csv_name: str, lock_key: str):
    if not production_exports_available():
        pytest.skip("Production exports not available")
    frame = assert_csv_contract(MARTS_DIR / csv_name, min_rows=1)
    assert len(frame) == WEEK2_LOCKED[lock_key]


@pytest.mark.exports
def test_production_exports_mirror_marts_csvs():
    if not production_exports_available():
        pytest.skip("Production exports not available")
    for csv_name in (
        "campaign_kpis.csv",
        "ctr_trends.csv",
        "segment_performance.csv",
        "ab_test_results.csv",
        "forecast_results.csv",
        "recommendation_matrix.csv",
    ):
        marts_text = (MARTS_DIR / csv_name).read_text(encoding="utf-8")
        exports_text = (EXPORTS_DIR / csv_name).read_text(encoding="utf-8")
        assert marts_text == exports_text


@pytest.mark.exports
def test_production_tableau_manifest_lists_all_csvs():
    if not production_exports_available():
        pytest.skip("Production exports not available")
    manifest = json.loads((EXPORTS_DIR / "tableau_data_manifest.json").read_text(encoding="utf-8"))
    manifest_names = {item["file"] for item in manifest["files"]}
    assert manifest_names == {
        "campaign_kpis.csv",
        "ctr_trends.csv",
        "segment_performance.csv",
        "ab_test_results.csv",
        "forecast_results.csv",
        "recommendation_matrix.csv",
    }


@pytest.mark.excel
def test_production_excel_workbook_contract():
    if not production_exports_available():
        pytest.skip("Production exports not available")
    if not EXCEL_WORKBOOK.exists():
        pytest.skip("Local Excel workbook not generated")
    assert_excel_workbook_contract(EXCEL_WORKBOOK)


@pytest.mark.recommendations
def test_production_recommendations_summary_counts():
    if not RECOMMENDATIONS_SUMMARY.exists():
        pytest.skip("Production recommendations summary not available")
    payload = json.loads(RECOMMENDATIONS_SUMMARY.read_text(encoding="utf-8"))
    assert payload["recommendation_count"] == WEEK2_LOCKED["recommendation_count"]
    assert payload["action_counts"]["scale"] == WEEK2_LOCKED["recommendation_scale"]
    assert payload["action_counts"]["pause"] == WEEK2_LOCKED["recommendation_pause"]
    assert payload["action_counts"]["retest"] == WEEK2_LOCKED["recommendation_retest"]


def test_production_export_summary_matches_lock():
    if not production_exports_available():
        pytest.skip("Production exports not available")
    payload = json.loads(EXPORT_DASHBOARD_SUMMARY.read_text(encoding="utf-8"))
    assert payload["export_count"] == WEEK2_LOCKED["export_count"]
    assert payload["success"] is True


def test_production_segment_click_share_sums_to_one(duckdb_connection):
    if not production_marts_populated():
        pytest.skip("Production marts not populated")
    total_share = duckdb_connection.execute(
        "SELECT SUM(click_share) FROM mart_device_app_performance"
    ).fetchone()[0]
    assert_approx_ratio(float(total_share), 1.0, 0.01)


def test_production_validation_summary_available():
    if not production_validation_summary_available():
        pytest.skip("Production validation summary not available")
    assert production_validation_summary_available() is True
