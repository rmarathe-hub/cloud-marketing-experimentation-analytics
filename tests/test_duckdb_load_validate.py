"""load_to_duckdb.py and validate_data.py tests."""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pandas as pd
import pytest

import create_duckdb_database as db_setup
import load_to_duckdb as loader
import validate_data as validator
from clean_avazu_ads import clean_avazu_ads
from clean_hillstrom_email import clean_hillstrom_email
from helpers import DOCS_DIR, PROJECT_ROOT, read_text, tiny_avazu_dataframe, tiny_hillstrom_dataframe
from paths import SQL_DIR

pytestmark = pytest.mark.unit


def _build_tiny_dataset_bundle(tmp_path: Path) -> dict[str, Path]:
    raw_dir = tmp_path / "data" / "raw"
    processed_dir = tmp_path / "data" / "processed"
    raw_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)

    avazu_raw = raw_dir / "avazu_train.csv"
    hillstrom_raw = raw_dir / "hillstrom_email.csv"
    tiny_avazu_dataframe().to_csv(avazu_raw, index=False)
    tiny_hillstrom_dataframe().to_csv(hillstrom_raw, index=False)

    avazu_clean, avazu_summary = clean_avazu_ads(pd.read_csv(avazu_raw))
    hillstrom_clean, hillstrom_summary = clean_hillstrom_email(pd.read_csv(hillstrom_raw))

    avazu_parquet = processed_dir / "avazu_clean.parquet"
    hillstrom_parquet = processed_dir / "hillstrom_clean.parquet"
    avazu_clean.to_parquet(avazu_parquet, index=False)
    hillstrom_clean.to_parquet(hillstrom_parquet, index=False)

    profile_summary = {
        "datasets": {
            "avazu": {
                "row_count": len(pd.read_csv(avazu_raw)),
            },
            "hillstrom": {
                "row_count": len(pd.read_csv(hillstrom_raw)),
            },
        }
    }
    cleaning_summary = {
        "datasets": {
            "avazu": {**avazu_summary, "input_rows": len(pd.read_csv(avazu_raw))},
            "hillstrom": {**hillstrom_summary, "input_rows": len(pd.read_csv(hillstrom_raw))},
        }
    }

    profile_path = processed_dir / "raw_profile_summary.json"
    cleaning_path = processed_dir / "cleaning_summary.json"
    profile_path.write_text(json.dumps(profile_summary))
    cleaning_path.write_text(json.dumps(cleaning_summary))

    return {
        "db_path": processed_dir / "marketing_analytics.duckdb",
        "avazu_raw": avazu_raw,
        "hillstrom_raw": hillstrom_raw,
        "avazu_parquet": avazu_parquet,
        "hillstrom_parquet": hillstrom_parquet,
        "profile_path": profile_path,
        "cleaning_path": cleaning_path,
    }


def test_load_module_imports_without_database_connection():
    assert hasattr(loader, "main")
    assert hasattr(loader, "load_data")
    assert hasattr(loader, "get_load_targets")


def test_validate_module_imports_without_database_connection():
    assert hasattr(validator, "main")
    assert hasattr(validator, "run_validation")


def test_get_load_targets_paths():
    targets = loader.get_load_targets()
    assert [target.table_name for target in targets] == list(loader.LOAD_TABLES)
    assert targets[0].source_type == "csv"
    assert targets[2].source_type == "parquet"


def test_validate_local_sources_missing_file(tmp_path):
    missing = tmp_path / "missing.csv"
    targets = [loader.LoadTarget("raw_avazu_ads", "raw", missing, "csv")]

    with pytest.raises(FileNotFoundError, match="Missing required local files"):
        loader.validate_local_sources(targets)


def test_ensure_database_ready_missing_db(tmp_path):
    config = db_setup.DatabaseConfig(database_path=tmp_path / "missing.duckdb")

    with pytest.raises(RuntimeError, match="database not found"):
        loader.ensure_database_ready(config)


def test_load_and_validate_tiny_pipeline(tmp_path):
    bundle = _build_tiny_dataset_bundle(tmp_path)
    config = db_setup.DatabaseConfig(database_path=bundle["db_path"])
    db_setup.create_database(config=config, sql_dir=SQL_DIR)

    targets = loader.get_load_targets(
        avazu_raw=bundle["avazu_raw"],
        hillstrom_raw=bundle["hillstrom_raw"],
        avazu_clean=bundle["avazu_parquet"],
        hillstrom_clean=bundle["hillstrom_parquet"],
    )
    load_summary = loader.load_data(
        config=config,
        targets=targets,
        summary_path=tmp_path / "duckdb_load_summary.json",
    )
    assert load_summary["success"] is True
    assert load_summary["loaded_table_count"] == 4

    expectations = validator.load_expectations(
        profile_path=bundle["profile_path"],
        cleaning_path=bundle["cleaning_path"],
    )
    validation_summary = validator.run_validation(
        config=config,
        expectations=expectations,
        summary_path=tmp_path / "data_validation_summary.json",
    )
    assert validation_summary["success"] is True
    assert validation_summary["failed_count"] == 0


def test_load_data_is_safe_to_rerun(tmp_path):
    bundle = _build_tiny_dataset_bundle(tmp_path)
    config = db_setup.DatabaseConfig(database_path=bundle["db_path"])
    db_setup.create_database(config=config, sql_dir=SQL_DIR)
    targets = loader.get_load_targets(
        avazu_raw=bundle["avazu_raw"],
        hillstrom_raw=bundle["hillstrom_raw"],
        avazu_clean=bundle["avazu_parquet"],
        hillstrom_clean=bundle["hillstrom_parquet"],
    )

    summary_path = tmp_path / "duckdb_load_summary.json"
    first = loader.load_data(config=config, targets=targets, summary_path=summary_path)
    second = loader.load_data(config=config, targets=targets, summary_path=summary_path)

    assert first["success"] and second["success"]
    assert first["loads"][0]["row_count"] == second["loads"][0]["row_count"]


def test_mart_tables_remain_empty_after_load(tmp_path):
    bundle = _build_tiny_dataset_bundle(tmp_path)
    config = db_setup.DatabaseConfig(database_path=bundle["db_path"])
    db_setup.create_database(config=config, sql_dir=SQL_DIR)
    loader.load_data(
        config=config,
        targets=loader.get_load_targets(
            avazu_raw=bundle["avazu_raw"],
            hillstrom_raw=bundle["hillstrom_raw"],
            avazu_clean=bundle["avazu_parquet"],
            hillstrom_clean=bundle["hillstrom_parquet"],
        ),
        summary_path=tmp_path / "duckdb_load_summary.json",
    )

    connection = duckdb.connect(str(bundle["db_path"]), read_only=True)
    try:
        for table_name in validator.MART_TABLES:
            count = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            assert count == 0
    finally:
        connection.close()


def test_validation_summary_schema(tmp_path):
    bundle = _build_tiny_dataset_bundle(tmp_path)
    config = db_setup.DatabaseConfig(database_path=bundle["db_path"])
    db_setup.create_database(config=config, sql_dir=SQL_DIR)
    loader.load_data(
        config=config,
        targets=loader.get_load_targets(
            avazu_raw=bundle["avazu_raw"],
            hillstrom_raw=bundle["hillstrom_raw"],
            avazu_clean=bundle["avazu_parquet"],
            hillstrom_clean=bundle["hillstrom_parquet"],
        ),
        summary_path=tmp_path / "duckdb_load_summary.json",
    )

    summary = validator.run_validation(
        config=config,
        expectations=validator.load_expectations(
            profile_path=bundle["profile_path"],
            cleaning_path=bundle["cleaning_path"],
        ),
        summary_path=tmp_path / "data_validation_summary.json",
    )

    assert "checks" in summary
    assert summary["passed_count"] >= 1
    assert all("check_name" in check for check in summary["checks"])


def test_readme_marks_day6_complete_not_week2():
    readme = read_text(PROJECT_ROOT / "README.md")
    assert "DuckDB load + validation | ✅ Complete" in readme
    assert "Campaign KPI marts | 🔲 Pending" in readme


def test_validate_script_exists_load_script_exists():
    assert (PROJECT_ROOT / "scripts" / "load_to_duckdb.py").exists()
    assert (PROJECT_ROOT / "scripts" / "validate_data.py").exists()
    assert not (PROJECT_ROOT / "scripts" / "run_campaign_kpis.py").exists()


def test_duckdb_setup_doc_mentions_day6_load():
    content = read_text(DOCS_DIR / "duckdb_setup.md").lower()
    for term in ["load_to_duckdb", "validate_data", "day 6"]:
        assert term in content
