"""Week 1 foundation lock and integration tests."""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pandas as pd
import pytest

import create_duckdb_database as db_setup
import generate_week1_data_lock as week1_lock
import load_to_duckdb as loader
import validate_data as validator
from helpers import run_implemented_week2_analytics
from clean_avazu_ads import clean_avazu_ads
from clean_hillstrom_email import clean_hillstrom_email
from cleaning_utils import merge_cleaning_summary
from helpers import (
    DOCS_DIR,
    PROJECT_ROOT,
    REQUIRED_SCRIPTS,
    read_text,
    tiny_avazu_dataframe,
    tiny_hillstrom_dataframe,
)
from paths import SQL_DIR, WEEK1_DATA_LOCK_DOC
from profile_raw_data import profile_avazu_dataframe, profile_hillstrom_dataframe, write_profile_summary

pytestmark = [pytest.mark.week1, pytest.mark.integration]

WEEK1_LOCKED_STATS = {
    "avazu_rows": 500_000,
    "hillstrom_rows": 64_000,
    "avazu_ctr_pct": 16.4074,
    "hillstrom_visit_rate_pct": 14.6781,
    "hillstrom_conversion_rate_pct": 0.9031,
    "control_recipients": 21_306,
    "mens_email_recipients": 21_307,
    "womens_email_recipients": 21_387,
}


WEEK1_SCRIPT_NAMES = [
    "download_or_import_data.py",
    "profile_raw_data.py",
    "clean_avazu_ads.py",
    "clean_hillstrom_email.py",
    "upload_to_s3.py",
    "create_duckdb_database.py",
    "load_to_duckdb.py",
    "validate_data.py",
    "generate_week1_data_lock.py",
]


def test_week1_data_lock_doc_exists():
    assert WEEK1_DATA_LOCK_DOC.is_file()


@pytest.mark.parametrize(
    "term",
    [
        "Status:** Locked",
        "500,000",
        "64,000",
        "16.4074%",
        "14.6781%",
        "control",
        "mens_email",
        "womens_email",
        "Week 2 boundary",
        "week2_analytics_lock.md",
        "generate_week1_data_lock.py",
    ],
)
def test_week1_data_lock_contains_frozen_stats(term: str):
    content = read_text(WEEK1_DATA_LOCK_DOC)
    assert term in content


def test_week1_required_scripts_exist():
    for script_name in WEEK1_SCRIPT_NAMES:
        assert (PROJECT_ROOT / "scripts" / script_name).is_file()
    assert REQUIRED_SCRIPTS  # sanity: helpers list is non-empty


def test_week2_pending_scripts_do_not_exist():
    from helpers import WEEK2_SCRIPTS_PENDING

    for script_name in WEEK2_SCRIPTS_PENDING:
        assert not (PROJECT_ROOT / "scripts" / script_name).exists()


def test_week2_day13_export_script_exists():
    assert (PROJECT_ROOT / "scripts" / "export_dashboard_data.py").exists()
    assert (PROJECT_ROOT / "scripts" / "generate_week2_analytics_lock.py").exists()


def test_readme_marks_week1_lock_complete():
    readme = read_text(PROJECT_ROOT / "README.md")
    assert "Week 1 tests + docs lock | ✅ Complete" in readme
    assert "Campaign KPI marts | ✅ Complete" in readme
    assert "Funnel + segment analysis | ✅ Complete" in readme
    assert "A/B test analysis | ✅ Complete" in readme
    assert "CTR forecasting | ✅ Complete" in readme


def _build_week1_summaries(tmp_path: Path) -> dict[str, Path]:
    processed = tmp_path / "data" / "processed"
    processed.mkdir(parents=True)

    profile = {
        "datasets": {
            "avazu": {"row_count": 3},
            "hillstrom": {"row_count": 4},
        }
    }
    cleaning = {
        "datasets": {
            "avazu": {
                "output_rows": 2,
                "ctr": 0.5,
                "rows_removed": 1,
                "date_range": {
                    "min_event_date": "2014-10-21",
                    "max_event_date": "2014-10-21",
                },
            },
            "hillstrom": {
                "output_rows": 4,
                "visit_rate": 0.25,
                "conversion_rate": 0.1,
                "rows_removed": 0,
                "treatment_group_counts": {
                    "control": 1,
                    "mens_email": 2,
                    "womens_email": 1,
                },
            },
        }
    }
    load = {
        "database_path": "data/processed/marketing_analytics.duckdb",
        "loads": [
            {"table_name": "raw_avazu_ads", "row_count": 3, "status": "success"},
            {"table_name": "stg_email_experiment", "row_count": 4, "status": "success"},
        ],
    }
    validation = {
        "success": True,
        "passed_count": 2,
        "failed_count": 0,
        "checks": [
            {"check_name": "raw_avazu_ads_row_count", "status": "pass"},
            {"check_name": "stg_email_experiment_row_count", "status": "pass"},
        ],
    }

    paths = {
        "profile": processed / "raw_profile_summary.json",
        "cleaning": processed / "cleaning_summary.json",
        "load": processed / "duckdb_load_summary.json",
        "validation": processed / "data_validation_summary.json",
    }
    paths["profile"].write_text(json.dumps(profile))
    paths["cleaning"].write_text(json.dumps(cleaning))
    paths["load"].write_text(json.dumps(load))
    paths["validation"].write_text(json.dumps(validation))
    return paths


def test_generate_week1_data_lock_from_summaries(tmp_path, monkeypatch):
    summaries = _build_week1_summaries(tmp_path)
    monkeypatch.setattr(week1_lock, "RAW_PROFILE_SUMMARY", summaries["profile"])
    monkeypatch.setattr(week1_lock, "CLEANING_SUMMARY", summaries["cleaning"])
    monkeypatch.setattr(week1_lock, "DUCKDB_LOAD_SUMMARY", summaries["load"])
    monkeypatch.setattr(week1_lock, "DATA_VALIDATION_SUMMARY", summaries["validation"])
    monkeypatch.setattr(week1_lock, "S3_UPLOAD_SUMMARY", tmp_path / "missing.json")

    output = tmp_path / "week1_data_lock.md"
    week1_lock.generate_week1_data_lock(output_path=output)

    content = output.read_text()
    assert "Status:** Locked" in content
    assert "500" not in content  # uses tiny summary values, not production constants
    assert "Visit rate | 25.0000%" in content


def test_generate_week1_data_lock_fails_without_validation_success(tmp_path, monkeypatch):
    summaries = _build_week1_summaries(tmp_path)
    validation = json.loads(summaries["validation"].read_text())
    validation["success"] = False
    summaries["validation"].write_text(json.dumps(validation))

    monkeypatch.setattr(week1_lock, "RAW_PROFILE_SUMMARY", summaries["profile"])
    monkeypatch.setattr(week1_lock, "CLEANING_SUMMARY", summaries["cleaning"])
    monkeypatch.setattr(week1_lock, "DUCKDB_LOAD_SUMMARY", summaries["load"])
    monkeypatch.setattr(week1_lock, "DATA_VALIDATION_SUMMARY", summaries["validation"])

    with pytest.raises(RuntimeError, match="Validation summary indicates failures"):
        week1_lock.generate_week1_data_lock(output_path=tmp_path / "lock.md")


def test_week1_end_to_end_smoke_on_tiny_data(tmp_path: Path):
    raw_dir = tmp_path / "data" / "raw"
    processed_dir = tmp_path / "data" / "processed"
    raw_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)

    avazu_raw = raw_dir / "avazu_train.csv"
    hillstrom_raw = raw_dir / "hillstrom_email.csv"
    tiny_avazu_dataframe().to_csv(avazu_raw, index=False)
    tiny_hillstrom_dataframe().to_csv(hillstrom_raw, index=False)

    avazu_df = pd.read_csv(avazu_raw)
    hillstrom_df = pd.read_csv(hillstrom_raw)

    profile = {
        "generated_at": "test",
        "datasets": {
            "avazu": profile_avazu_dataframe(avazu_df),
            "hillstrom": profile_hillstrom_dataframe(hillstrom_df),
        },
    }
    profile_path = processed_dir / "raw_profile_summary.json"
    write_profile_summary(profile, profile_path)

    avazu_clean, avazu_summary = clean_avazu_ads(avazu_df)
    hillstrom_clean, hillstrom_summary = clean_hillstrom_email(hillstrom_df)
    avazu_parquet = processed_dir / "avazu_clean.parquet"
    hillstrom_parquet = processed_dir / "hillstrom_clean.parquet"
    avazu_clean.to_parquet(avazu_parquet, index=False)
    hillstrom_clean.to_parquet(hillstrom_parquet, index=False)

    cleaning_path = processed_dir / "cleaning_summary.json"
    merge_cleaning_summary("avazu", avazu_summary, summary_path=cleaning_path)
    merge_cleaning_summary("hillstrom", hillstrom_summary, summary_path=cleaning_path)

    db_path = processed_dir / "marketing_analytics.duckdb"
    config = db_setup.DatabaseConfig(database_path=db_path)
    db_setup.create_database(config=config, sql_dir=SQL_DIR)

    targets = loader.get_load_targets(
        avazu_raw=avazu_raw,
        hillstrom_raw=hillstrom_raw,
        avazu_clean=avazu_parquet,
        hillstrom_clean=hillstrom_parquet,
    )
    load_summary = loader.load_data(
        config=config,
        targets=targets,
        summary_path=processed_dir / "duckdb_load_summary.json",
    )
    assert load_summary["success"] is True

    run_implemented_week2_analytics(config, processed_dir)

    validation_summary = validator.run_validation(
        config=config,
        expectations=validator.load_expectations(
            profile_path=profile_path,
            cleaning_path=cleaning_path,
        ),
        summary_path=processed_dir / "data_validation_summary.json",
    )
    assert validation_summary["success"] is True

    connection = duckdb.connect(str(db_path), read_only=True)
    try:
        mart_count = connection.execute(
            "SELECT COUNT(*) FROM mart_campaign_kpis"
        ).fetchone()[0]
        assert mart_count > 0
    finally:
        connection.close()


def test_locked_doc_matches_contract_constants():
    content = read_text(WEEK1_DATA_LOCK_DOC)
    assert f"{WEEK1_LOCKED_STATS['avazu_rows']:,}" in content
    assert f"{WEEK1_LOCKED_STATS['hillstrom_rows']:,}" in content
    assert f"{WEEK1_LOCKED_STATS['avazu_ctr_pct']:.4f}%" in content
    assert f"{WEEK1_LOCKED_STATS['hillstrom_visit_rate_pct']:.4f}%" in content
