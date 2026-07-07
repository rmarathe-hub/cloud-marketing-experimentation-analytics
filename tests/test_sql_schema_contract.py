"""SQL schema contract tests for DuckDB Week 1 setup."""

from __future__ import annotations

import pytest

from helpers import (
    DUCKDB_ALL_TABLES,
    DUCKDB_MART_TABLES,
    DUCKDB_RAW_TABLES,
    DUCKDB_STAGING_TABLES,
    PROJECT_ROOT,
    SQL_SCHEMA_FILES,
    read_text,
)

pytestmark = [pytest.mark.duckdb, pytest.mark.unit, pytest.mark.week1]

SQL_DIR = PROJECT_ROOT / "sql"


@pytest.mark.parametrize("sql_file", SQL_SCHEMA_FILES)
def test_sql_schema_file_exists(sql_file: str) -> None:
    assert (SQL_DIR / sql_file).is_file()


@pytest.mark.parametrize("sql_file", SQL_SCHEMA_FILES)
def test_sql_schema_uses_create_table_if_not_exists(sql_file: str) -> None:
    content = read_text(SQL_DIR / sql_file).upper()
    assert "CREATE TABLE IF NOT EXISTS" in content


@pytest.mark.parametrize("table_name", DUCKDB_RAW_TABLES)
def test_raw_table_defined_in_sql(table_name: str) -> None:
    content = read_text(SQL_DIR / "01_raw_tables.sql").lower()
    assert table_name in content


@pytest.mark.parametrize("table_name", DUCKDB_STAGING_TABLES)
def test_staging_table_defined_in_sql(table_name: str) -> None:
    content = read_text(SQL_DIR / "02_staging_tables.sql").lower()
    assert table_name in content


@pytest.mark.parametrize("table_name", DUCKDB_MART_TABLES)
def test_mart_table_defined_in_sql(table_name: str) -> None:
    content = read_text(SQL_DIR / "03_mart_tables.sql").lower()
    assert table_name in content


@pytest.mark.parametrize("table_name", DUCKDB_ALL_TABLES)
def test_table_name_unique_across_schema_files(table_name: str) -> None:
    hits = 0
    for sql_file in SQL_SCHEMA_FILES:
        if table_name in read_text(SQL_DIR / sql_file).lower():
            hits += 1
    assert hits == 1


def test_raw_avazu_sql_has_snake_case_anonymous_features() -> None:
    content = read_text(SQL_DIR / "01_raw_tables.sql").lower()
    for col in ["c1", "c14", "c21"]:
        assert col in content


def test_staging_avazu_sql_has_event_fields() -> None:
    content = read_text(SQL_DIR / "02_staging_tables.sql").lower()
    assert "event_date" in content
    assert "event_hour" in content
    assert "flag_missing_fields" in content


def test_staging_hillstrom_sql_has_treatment_fields() -> None:
    content = read_text(SQL_DIR / "02_staging_tables.sql").lower()
    for col in ["treatment_group", "treatment_label", "converted", "revenue", "zip_code_std"]:
        assert col in content


def test_mart_sql_does_not_include_insert_statements() -> None:
    for sql_file in SQL_SCHEMA_FILES:
        content = read_text(SQL_DIR / sql_file).upper()
        assert "INSERT INTO" not in content


@pytest.mark.parametrize("mart_table", DUCKDB_MART_TABLES)
def test_mart_sql_is_placeholder_only(mart_table: str) -> None:
    content = read_text(SQL_DIR / "03_mart_tables.sql")
    assert f"CREATE TABLE IF NOT EXISTS {mart_table}" in content
