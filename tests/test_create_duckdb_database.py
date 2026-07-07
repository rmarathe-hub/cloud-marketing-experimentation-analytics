"""create_duckdb_database.py tests using temporary local databases."""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pytest

import create_duckdb_database as db_setup
from helpers import DOCS_DIR, PROJECT_ROOT, read_text
from paths import SQL_DIR

pytestmark = pytest.mark.unit


def test_module_imports_without_database_connection():
    assert hasattr(db_setup, "main")
    assert hasattr(db_setup, "load_config")
    assert hasattr(db_setup, "create_database")
    assert hasattr(db_setup, "EXPECTED_TABLES")


def test_load_config_uses_duckdb_path_from_env(monkeypatch, tmp_path):
    db_path = tmp_path / "custom.duckdb"
    monkeypatch.setenv("DUCKDB_PATH", str(db_path))

    config = db_setup.load_config()

    assert config.database_path == db_path


def test_load_config_defaults_when_env_missing(monkeypatch):
    monkeypatch.delenv("DUCKDB_PATH", raising=False)

    config = db_setup.load_config()

    assert config.database_path.name == "marketing_analytics.duckdb"
    assert config.database_path.parent.name == "processed"


def test_expected_tables_list_is_correct():
    assert set(db_setup.EXPECTED_TABLES) == {
        "raw_avazu_ads",
        "raw_hillstrom_email",
        "stg_ad_events",
        "stg_email_experiment",
        "mart_campaign_kpis",
        "mart_ctr_trends",
        "mart_device_app_performance",
        "mart_ab_test_results",
        "mart_forecast_inputs",
        "mart_forecast_results",
    }
    assert db_setup.EXPECTED_TABLES["raw_avazu_ads"] == "raw"
    assert db_setup.EXPECTED_TABLES["stg_ad_events"] == "staging"
    assert db_setup.EXPECTED_TABLES["mart_campaign_kpis"] == "mart"


def test_get_schema_files_returns_ordered_sql_files():
    files = db_setup.get_schema_files(SQL_DIR)
    assert [path.name for path in files] == list(db_setup.SCHEMA_FILES)


def test_get_schema_files_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="Missing required SQL schema files"):
        db_setup.get_schema_files(tmp_path)


def test_create_database_builds_empty_tables(tmp_path):
    db_path = tmp_path / "marketing_analytics.duckdb"
    summary_path = tmp_path / "duckdb_setup_summary.json"
    config = db_setup.DatabaseConfig(database_path=db_path)

    summary = db_setup.create_database(
        config=config,
        sql_dir=SQL_DIR,
        summary_path=summary_path,
    )

    assert summary["success"] is True
    assert summary["table_count"] == 10
    assert summary["data_loaded"] is False
    assert all(table["row_count"] == 0 for table in summary["tables"])

    connection = duckdb.connect(str(db_path), read_only=True)
    try:
        tables = connection.execute("SHOW TABLES").fetchall()
        table_names = {row[0] for row in tables}
        assert table_names == set(db_setup.EXPECTED_TABLES)
    finally:
        connection.close()

    payload = json.loads(summary_path.read_text())
    assert payload["table_count"] == 10
    assert payload["success"] is True


def test_create_database_is_safe_to_rerun(tmp_path):
    db_path = tmp_path / "marketing_analytics.duckdb"
    config = db_setup.DatabaseConfig(database_path=db_path)

    first = db_setup.create_database(config=config, sql_dir=SQL_DIR)
    second = db_setup.create_database(config=config, sql_dir=SQL_DIR)

    assert first["table_count"] == second["table_count"] == 10


def test_sql_schema_files_exist():
    for filename in db_setup.SCHEMA_FILES:
        assert (SQL_DIR / filename).is_file()


def test_duckdb_setup_doc_exists_with_day6_warning():
    content = read_text(DOCS_DIR / "duckdb_setup.md").lower()
    for term in [
        "duckdb",
        "day 6",
        "create table",
        "raw_avazu_ads",
        "stg_ad_events",
        "mart_campaign_kpis",
        "gitignore",
        "glue",
        "lambda",
        "redshift",
        "athena",
    ]:
        assert term in content


def test_readme_marks_duckdb_warehouse_complete_not_load():
    readme = read_text(PROJECT_ROOT / "README.md")
    assert "DuckDB warehouse setup | ✅ Complete" in readme
    assert "DuckDB load + validation | 🔲 Pending" in readme
    assert "DuckDB load + validation | ✅ Complete" not in readme


def test_load_to_duckdb_script_not_created_yet():
    assert not (PROJECT_ROOT / "scripts" / "load_to_duckdb.py").exists()
