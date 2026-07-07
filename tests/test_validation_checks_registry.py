"""validate_data.py check registry and failure-mode tests."""

from __future__ import annotations

import json

import duckdb
import pandas as pd
import pytest

import create_duckdb_database as db_setup
import load_to_duckdb as loader
import validate_data as validator
from clean_avazu_ads import clean_avazu_ads
from helpers import VALIDATION_CHECK_NAMES, WEEK1_LOCKED, tiny_avazu_dataframe, write_tiny_avazu_csv
from paths import SQL_DIR

pytestmark = [pytest.mark.unit, pytest.mark.duckdb, pytest.mark.week2]


def _tiny_avazu_bundle(tmp_path):
    raw_dir = tmp_path / "raw"
    processed = tmp_path / "processed"
    raw_dir.mkdir(parents=True)
    processed.mkdir(parents=True)
    avazu_raw = write_tiny_avazu_csv(raw_dir / "avazu_train.csv")
    avazu_clean, avazu_summary = clean_avazu_ads(pd.read_csv(avazu_raw))
    parquet = processed / "avazu_clean.parquet"
    avazu_clean.to_parquet(parquet, index=False)
    config = db_setup.DatabaseConfig(database_path=processed / "test.duckdb")
    db_setup.create_database(config=config, sql_dir=SQL_DIR)
    loader.load_data(
        config=config,
        targets=[loader.LoadTarget("stg_ad_events", "staging", parquet, "parquet")],
        summary_path=processed / "duckdb_load_summary.json",
    )
    return config, avazu_summary, len(avazu_clean)


@pytest.mark.parametrize("check_name", VALIDATION_CHECK_NAMES)
def test_validation_check_name_is_snake_case(check_name: str) -> None:
    assert check_name == check_name.lower()
    assert " " not in check_name


def test_validation_registry_has_twenty_five_checks() -> None:
    assert len(VALIDATION_CHECK_NAMES) == 25
    assert len(set(VALIDATION_CHECK_NAMES)) == 25


def test_validation_summary_lists_all_check_names(tmp_path):
    config, avazu_summary, staging_rows = _tiny_avazu_bundle(tmp_path)
    expectations = {
        "profile": {"avazu": {"row_count": staging_rows}, "hillstrom": {"row_count": 0}},
        "cleaning": {
            "avazu": {
                "input_rows": staging_rows,
                "output_rows": staging_rows,
                "ctr": avazu_summary["ctr"],
            },
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
        summary_path=tmp_path / "validation.json",
    )
    returned_names = {check["check_name"] for check in summary["checks"]}
    for check_name in VALIDATION_CHECK_NAMES:
        assert check_name in returned_names


def test_validation_fails_on_wrong_staging_count(tmp_path):
    config, avazu_summary, staging_rows = _tiny_avazu_bundle(tmp_path)
    expectations = {
        "profile": {"avazu": {"row_count": staging_rows}, "hillstrom": {"row_count": 0}},
        "cleaning": {
            "avazu": {
                "input_rows": staging_rows,
                "output_rows": staging_rows + 1,
                "ctr": avazu_summary["ctr"],
            },
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
        summary_path=tmp_path / "validation.json",
    )
    failed = [c for c in summary["checks"] if c["status"] != "pass"]
    assert any(c["check_name"] == "stg_ad_events_row_count" for c in failed)


@pytest.mark.data
@pytest.mark.slow
def test_production_validation_summary_has_twenty_five_passing_checks():
    from helpers import production_validation_summary_available
    from paths import DATA_VALIDATION_SUMMARY

    if not production_validation_summary_available():
        pytest.skip("Production validation summary not available")
    payload = json.loads(DATA_VALIDATION_SUMMARY.read_text(encoding="utf-8"))
    assert payload["passed_count"] == WEEK1_LOCKED["validation_check_count"]
    assert payload["success"] is True
    names = {check["check_name"] for check in payload["checks"]}
    assert names == set(VALIDATION_CHECK_NAMES)
