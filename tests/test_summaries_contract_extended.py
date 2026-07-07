"""Extended summary JSON contract tests."""

from __future__ import annotations

import pytest

from helpers import (
    CLEANING_SUMMARY,
    RAW_PROFILE_SUMMARY,
    WEEK1_LOCKED,
    assert_approx_ratio,
    load_json,
    production_load_summary_available,
    production_validation_summary_available,
)
from paths import DATA_VALIDATION_SUMMARY, DUCKDB_LOAD_SUMMARY, S3_UPLOAD_SUMMARY

pytestmark = [pytest.mark.week1, pytest.mark.unit]


@pytest.mark.data
@pytest.mark.slow
def test_raw_profile_summary_contract():
    if not RAW_PROFILE_SUMMARY.exists():
        pytest.skip("raw_profile_summary.json not present locally")
    payload = load_json(RAW_PROFILE_SUMMARY)
    avazu = payload["datasets"]["avazu"]
    hillstrom = payload["datasets"]["hillstrom"]
    assert avazu["row_count"] == WEEK1_LOCKED["avazu_rows"]
    assert avazu["click_distribution"]["click"] == WEEK1_LOCKED["avazu_clicks"]
    assert_approx_ratio(avazu["ctr"], WEEK1_LOCKED["avazu_ctr_ratio"])
    assert hillstrom["row_count"] == WEEK1_LOCKED["hillstrom_rows"]
    assert_approx_ratio(hillstrom["visit_rate"], WEEK1_LOCKED["hillstrom_visit_rate_ratio"])
    assert_approx_ratio(hillstrom["conversion_rate"], WEEK1_LOCKED["hillstrom_conversion_rate_ratio"])


@pytest.mark.data
@pytest.mark.slow
def test_cleaning_summary_contract():
    if not CLEANING_SUMMARY.exists():
        pytest.skip("cleaning_summary.json not present locally")
    payload = load_json(CLEANING_SUMMARY)
    avazu = payload["datasets"]["avazu"]
    hillstrom = payload["datasets"]["hillstrom"]
    assert avazu["input_rows"] == WEEK1_LOCKED["avazu_rows"]
    assert avazu["output_rows"] == WEEK1_LOCKED["avazu_rows"]
    assert avazu["rows_removed"] == 0
    assert_approx_ratio(avazu["ctr"], WEEK1_LOCKED["avazu_ctr_ratio"])
    assert hillstrom["input_rows"] == WEEK1_LOCKED["hillstrom_rows"]
    assert hillstrom["output_rows"] == WEEK1_LOCKED["hillstrom_rows"]
    assert hillstrom["rows_removed"] == 0
    assert hillstrom["zip_code_typo_rows"] == WEEK1_LOCKED["hillstrom_zip_typo_rows"]
    assert hillstrom["treatment_group_counts"]["control"] == WEEK1_LOCKED["control_recipients"]


@pytest.mark.data
@pytest.mark.slow
@pytest.mark.parametrize(
    "table_name,expected_rows",
    [
        ("raw_avazu_ads", WEEK1_LOCKED["avazu_rows"]),
        ("raw_hillstrom_email", WEEK1_LOCKED["hillstrom_rows"]),
        ("stg_ad_events", WEEK1_LOCKED["avazu_rows"]),
        ("stg_email_experiment", WEEK1_LOCKED["hillstrom_rows"]),
    ],
)
def test_duckdb_load_summary_row_counts(table_name: str, expected_rows: int):
    if not production_load_summary_available():
        pytest.skip("Production duckdb_load_summary.json not present or appears to be test artifact")
    payload = load_json(DUCKDB_LOAD_SUMMARY)
    loads = {item["table_name"]: item for item in payload["loads"]}
    assert loads[table_name]["row_count"] == expected_rows
    assert loads[table_name]["status"] == "success"


@pytest.mark.data
@pytest.mark.slow
def test_validation_summary_contract():
    if not production_validation_summary_available():
        pytest.skip("Production data_validation_summary.json not present or invalid")
    payload = load_json(DATA_VALIDATION_SUMMARY)
    assert payload["success"] is True
    assert payload["passed_count"] == WEEK1_LOCKED["validation_check_count"]
    assert payload["failed_count"] == 0
    check_names = {item["check_name"] for item in payload["checks"]}
    assert "stg_ad_events_ctr" in check_names
    assert "stg_email_experiment_visit_rate" in check_names
    for mart_check in [c for c in payload["checks"] if c["check_name"].endswith("_empty")]:
        assert mart_check["status"] == "pass"


@pytest.mark.data
@pytest.mark.slow
def test_summaries_are_internally_consistent():
    if not production_load_summary_available() or not production_validation_summary_available():
        pytest.skip("Production summary files not present or appear to be test artifacts")
    profile = load_json(RAW_PROFILE_SUMMARY)
    cleaning = load_json(CLEANING_SUMMARY)
    load = load_json(DUCKDB_LOAD_SUMMARY)
    validation = load_json(DATA_VALIDATION_SUMMARY)
    assert profile["datasets"]["avazu"]["row_count"] == cleaning["datasets"]["avazu"]["input_rows"]
    assert cleaning["datasets"]["avazu"]["output_rows"] == next(
        item["row_count"] for item in load["loads"] if item["table_name"] == "stg_ad_events"
    )
    assert validation["success"] is True
    if S3_UPLOAD_SUMMARY.exists():
        s3 = load_json(S3_UPLOAD_SUMMARY)
        assert s3["uploaded_count"] == WEEK1_LOCKED["s3_upload_count"]
