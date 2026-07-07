"""Extended validate_data.py contract tests."""

from __future__ import annotations

import json

import duckdb
import pytest

import create_duckdb_database as db_setup
import load_to_duckdb as loader
import validate_data as validator
from helpers import WEEK1_LOCKED, load_json, production_validation_summary_available
from paths import DATA_VALIDATION_SUMMARY, SQL_DIR

pytestmark = [pytest.mark.duckdb, pytest.mark.unit, pytest.mark.week1]


def test_validate_module_exports_expected_functions():
    for name in ["main", "run_validation", "load_expectations", "write_validation_summary"]:
        assert hasattr(validator, name)


def test_validation_detects_row_count_mismatch(tmp_path):
    bundle_db = tmp_path / "db.duckdb"
    config = db_setup.DatabaseConfig(database_path=bundle_db)
    db_setup.create_database(config=config, sql_dir=SQL_DIR)
    connection = duckdb.connect(str(bundle_db))
    connection.execute(
        """
        INSERT INTO raw_avazu_ads (
            id, click, hour, c1, banner_pos, site_id, site_domain, site_category,
            app_id, app_domain, app_category, device_id, device_ip, device_model,
            device_type, device_conn_type, c14, c15, c16, c17, c18, c19, c20, c21
        ) VALUES (
            '1', 0, 14102108, 1, 0, 's', 's', 's', 'a', 'a', 'a', 'd', 'ip', 'm', 1, 2,
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0
        )
        """
    )
    connection.close()

    expectations = {
        "profile": {"avazu": {"row_count": 1}, "hillstrom": {"row_count": 0}},
        "cleaning": {
            "avazu": {"input_rows": 999, "output_rows": 0, "ctr": 0.0},
            "hillstrom": {
                "input_rows": 0,
                "output_rows": 0,
                "visit_rate": 0.0,
                "treatment_group_counts": {},
            },
        },
    }
    summary = validator.run_validation(
        config=config,
        expectations=expectations,
        summary_path=tmp_path / "data_validation_summary.json",
    )
    failed = [c for c in summary["checks"] if c["status"] != "pass"]
    assert failed
    assert any("row_count" in c["check_name"] for c in failed)


def test_validation_detects_non_empty_mart(tmp_path):
    bundle_db = tmp_path / "db.duckdb"
    config = db_setup.DatabaseConfig(database_path=bundle_db)
    db_setup.create_database(config=config, sql_dir=SQL_DIR)
    connection = duckdb.connect(str(bundle_db))
    connection.execute(
        "INSERT INTO mart_forecast_inputs (event_date, event_hour, impressions, clicks, ctr) "
        "VALUES ('2014-10-21', 8, 1, 1, 1.0)"
    )
    connection.close()

    expectations = {
        "profile": {"avazu": {"row_count": 0}, "hillstrom": {"row_count": 0}},
        "cleaning": {
            "avazu": {"input_rows": 0, "output_rows": 0, "ctr": 0.0},
            "hillstrom": {
                "input_rows": 0,
                "output_rows": 0,
                "visit_rate": 0.0,
                "treatment_group_counts": {},
            },
        },
    }
    summary = validator.run_validation(
        config=config,
        expectations=expectations,
        summary_path=tmp_path / "data_validation_summary.json",
    )
    mart_failures = [c for c in summary["checks"] if c["check_name"] == "mart_forecast_inputs_empty"]
    assert mart_failures
    assert mart_failures[0]["status"] == "fail"


def test_validation_summary_written_with_schema(tmp_path):
    bundle_db = tmp_path / "db.duckdb"
    config = db_setup.DatabaseConfig(database_path=bundle_db)
    db_setup.create_database(config=config, sql_dir=SQL_DIR)
    output = tmp_path / "validation.json"
    expectations = {
        "profile": {"avazu": {"row_count": 0}, "hillstrom": {"row_count": 0}},
        "cleaning": {
            "avazu": {"input_rows": 0, "output_rows": 0, "ctr": 0.0},
            "hillstrom": {
                "input_rows": 0,
                "output_rows": 0,
                "visit_rate": 0.0,
                "treatment_group_counts": {},
            },
        },
    }
    summary = validator.run_validation(
        config=config, expectations=expectations, summary_path=output
    )
    payload = json.loads(output.read_text())
    assert payload["success"] == summary["success"]
    assert "checks" in payload
    assert "passed_count" in payload


@pytest.mark.data
@pytest.mark.slow
def test_real_validation_summary_matches_lock():
    if not production_validation_summary_available():
        pytest.skip("Production validation summary not present or invalid")
    payload = load_json(DATA_VALIDATION_SUMMARY)
    assert len(payload["checks"]) == WEEK1_LOCKED["validation_check_count"]
    ctr_check = next(c for c in payload["checks"] if c["check_name"] == "stg_ad_events_ctr")
    visit_check = next(
        c for c in payload["checks"] if c["check_name"] == "stg_email_experiment_visit_rate"
    )
    assert ctr_check["status"] == "pass"
    assert visit_check["status"] == "pass"
    assert ctr_check["expected"] == WEEK1_LOCKED["avazu_ctr_ratio"]
    assert visit_check["expected"] == WEEK1_LOCKED["hillstrom_visit_rate_ratio"]
