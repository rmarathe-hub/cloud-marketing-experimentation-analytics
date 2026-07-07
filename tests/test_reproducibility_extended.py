"""Reproducibility and idempotency tests for Week 1 pipelines."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

import create_duckdb_database as db_setup
import generate_week1_data_lock as week1_lock
import load_to_duckdb as loader
import upload_to_s3 as uploader
from clean_avazu_ads import clean_avazu_ads
from clean_hillstrom_email import clean_hillstrom_email
from helpers import S3_UPLOAD_KEYS, tiny_avazu_dataframe, tiny_hillstrom_dataframe, write_tiny_avazu_csv
from paths import SQL_DIR

pytestmark = [pytest.mark.week1, pytest.mark.integration, pytest.mark.unit]


def test_avazu_cleaning_is_reproducible():
    df = tiny_avazu_dataframe()
    one, summary_one = clean_avazu_ads(df.copy())
    two, summary_two = clean_avazu_ads(df.copy())
    pd.testing.assert_frame_equal(one, two)
    assert summary_one["output_rows"] == summary_two["output_rows"]
    assert summary_one["ctr"] == summary_two["ctr"]


def test_hillstrom_cleaning_is_reproducible():
    df = tiny_hillstrom_dataframe()
    one, summary_one = clean_hillstrom_email(df.copy())
    two, summary_two = clean_hillstrom_email(df.copy())
    pd.testing.assert_frame_equal(one, two)
    assert summary_one["treatment_group_counts"] == summary_two["treatment_group_counts"]


def test_s3_key_generation_is_stable():
    config = uploader.UploadConfig(
        aws_profile="marketing-analytics",
        aws_region="us-east-1",
        bucket="bucket",
        raw_prefix="raw",
        processed_prefix="processed",
        marts_prefix="marts",
        export_prefix="exports",
    )
    keys_one = [t.s3_key for t in uploader.get_upload_targets(config)]
    keys_two = [t.s3_key for t in uploader.get_upload_targets(config)]
    assert keys_one == keys_two == list(S3_UPLOAD_KEYS)


def test_duckdb_schema_creation_is_idempotent(tmp_path):
    db_path = tmp_path / "marketing_analytics.duckdb"
    config = db_setup.DatabaseConfig(database_path=db_path)
    first = db_setup.create_database(config=config, sql_dir=SQL_DIR)
    second = db_setup.create_database(config=config, sql_dir=SQL_DIR)
    assert first["table_count"] == second["table_count"] == 10


def test_duckdb_load_is_idempotent(tmp_path):
    raw_dir = tmp_path / "raw"
    processed = tmp_path / "processed"
    raw_dir.mkdir()
    processed.mkdir()
    avazu_raw = write_tiny_avazu_csv(raw_dir / "avazu_train.csv")
    hillstrom_raw = raw_dir / "hillstrom_email.csv"
    tiny_hillstrom_dataframe().to_csv(hillstrom_raw, index=False)
    avazu_clean, _ = clean_avazu_ads(pd.read_csv(avazu_raw))
    hillstrom_clean, _ = clean_hillstrom_email(pd.read_csv(hillstrom_raw))
    avazu_parquet = processed / "avazu_clean.parquet"
    hillstrom_parquet = processed / "hillstrom_clean.parquet"
    avazu_clean.to_parquet(avazu_parquet, index=False)
    hillstrom_clean.to_parquet(hillstrom_parquet, index=False)

    db_path = processed / "marketing_analytics.duckdb"
    config = db_setup.DatabaseConfig(database_path=db_path)
    db_setup.create_database(config=config, sql_dir=SQL_DIR)
    targets = loader.get_load_targets(
        avazu_raw=avazu_raw,
        hillstrom_raw=hillstrom_raw,
        avazu_clean=avazu_parquet,
        hillstrom_clean=hillstrom_parquet,
    )
    summary_path = processed / "duckdb_load_summary.json"
    first = loader.load_data(config=config, targets=targets, summary_path=summary_path)
    second = loader.load_data(config=config, targets=targets, summary_path=summary_path)
    assert first["success"] and second["success"]
    assert first["loads"][0]["row_count"] == second["loads"][0]["row_count"]


def test_generate_lock_doc_is_deterministic_for_fixture(tmp_path, monkeypatch):
    processed = tmp_path / "processed"
    processed.mkdir()
    profile = {
        "datasets": {
            "avazu": {"row_count": 100},
            "hillstrom": {"row_count": 50},
        }
    }
    cleaning = {
        "datasets": {
            "avazu": {
                "output_rows": 100,
                "ctr": 0.1,
                "rows_removed": 0,
                "input_rows": 100,
                "date_range": {"min_event_date": "2014-10-21", "max_event_date": "2014-10-21"},
            },
            "hillstrom": {
                "output_rows": 50,
                "visit_rate": 0.2,
                "conversion_rate": 0.01,
                "rows_removed": 0,
                "input_rows": 50,
                "treatment_group_counts": {"control": 1, "mens_email": 2, "womens_email": 3},
            },
        }
    }
    load = {
        "database_path": "data/processed/marketing_analytics.duckdb",
        "loads": [{"table_name": "raw_avazu_ads", "row_count": 100, "status": "success"}],
    }
    validation = {
        "success": True,
        "passed_count": 1,
        "failed_count": 0,
        "checks": [{"check_name": "raw_avazu_ads_row_count", "status": "pass"}],
    }
    paths = {
        "profile": processed / "raw_profile_summary.json",
        "cleaning": processed / "cleaning_summary.json",
        "load": processed / "duckdb_load_summary.json",
        "validation": processed / "data_validation_summary.json",
    }
    for key, payload in [
        ("profile", profile),
        ("cleaning", cleaning),
        ("load", load),
        ("validation", validation),
    ]:
        paths[key].write_text(json.dumps(payload))
    monkeypatch.setattr(week1_lock, "RAW_PROFILE_SUMMARY", paths["profile"])
    monkeypatch.setattr(week1_lock, "CLEANING_SUMMARY", paths["cleaning"])
    monkeypatch.setattr(week1_lock, "DUCKDB_LOAD_SUMMARY", paths["load"])
    monkeypatch.setattr(week1_lock, "DATA_VALIDATION_SUMMARY", paths["validation"])
    monkeypatch.setattr(week1_lock, "S3_UPLOAD_SUMMARY", tmp_path / "missing.json")

    out = tmp_path / "lock.md"
    week1_lock.generate_week1_data_lock(output_path=out)
    first = out.read_text()
  # strip timestamp line for comparison
    lines = [line for line in first.splitlines() if not line.startswith("**Generated:**")]
    week1_lock.generate_week1_data_lock(output_path=out)
    second = out.read_text()
    second_lines = [line for line in second.splitlines() if not line.startswith("**Generated:**")]
    assert lines == second_lines


def test_cleaning_does_not_mutate_raw_csv(tmp_path):
    raw = write_tiny_avazu_csv(tmp_path / "avazu_train.csv")
    before = raw.read_bytes()
    clean_avazu_ads(pd.read_csv(raw))
    after = raw.read_bytes()
    assert before == after
