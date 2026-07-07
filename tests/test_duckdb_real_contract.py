"""Real DuckDB database contract tests."""

from __future__ import annotations

import duckdb
import pytest

from helpers import (
    DUCKDB_ALL_TABLES,
    DUCKDB_MART_TABLES,
    HILLSTROM_CLEAN_GROUPS,
    WEEK1_LOCKED,
    assert_approx_ratio,
    local_duckdb_available,
)
from paths import DUCKDB_DEFAULT_PATH

pytestmark = [pytest.mark.duckdb, pytest.mark.data, pytest.mark.slow, pytest.mark.integration]


@pytest.fixture(scope="module")
def duckdb_connection():
    if not local_duckdb_available():
        pytest.skip("Local DuckDB database not present")
    connection = duckdb.connect(str(DUCKDB_DEFAULT_PATH), read_only=True)
    yield connection
    connection.close()


@pytest.mark.parametrize("table_name", DUCKDB_ALL_TABLES)
def test_table_exists(duckdb_connection, table_name: str):
    count = duckdb_connection.execute(
        """
        SELECT COUNT(*) FROM information_schema.tables
        WHERE table_schema = 'main' AND table_name = ?
        """,
        [table_name],
    ).fetchone()[0]
    assert count == 1


@pytest.mark.parametrize(
    "table_name,expected_rows",
    [
        ("raw_avazu_ads", WEEK1_LOCKED["avazu_rows"]),
        ("raw_hillstrom_email", WEEK1_LOCKED["hillstrom_rows"]),
        ("stg_ad_events", WEEK1_LOCKED["avazu_rows"]),
        ("stg_email_experiment", WEEK1_LOCKED["hillstrom_rows"]),
    ],
)
def test_loaded_table_row_counts(duckdb_connection, table_name: str, expected_rows: int):
    actual = duckdb_connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    assert actual == expected_rows


@pytest.mark.parametrize("mart_table", DUCKDB_MART_TABLES)
def test_mart_tables_empty(duckdb_connection, mart_table: str):
    actual = duckdb_connection.execute(f"SELECT COUNT(*) FROM {mart_table}").fetchone()[0]
    assert actual == 0


def test_staging_avazu_ctr_matches_lock(duckdb_connection):
    ctr = duckdb_connection.execute(
        "SELECT AVG(CAST(click AS DOUBLE)) FROM stg_ad_events"
    ).fetchone()[0]
    assert_approx_ratio(float(ctr), WEEK1_LOCKED["avazu_ctr_ratio"])


def test_staging_hillstrom_visit_rate_matches_lock(duckdb_connection):
    rate = duckdb_connection.execute(
        "SELECT AVG(CAST(visit AS DOUBLE)) FROM stg_email_experiment"
    ).fetchone()[0]
    assert_approx_ratio(float(rate), WEEK1_LOCKED["hillstrom_visit_rate_ratio"])


@pytest.mark.parametrize("group,expected", list(HILLSTROM_CLEAN_GROUPS.items()))
def test_staging_hillstrom_treatment_counts(duckdb_connection, group: str, expected: int):
    actual = duckdb_connection.execute(
        "SELECT COUNT(*) FROM stg_email_experiment WHERE treatment_group = ?",
        [group],
    ).fetchone()[0]
    assert actual == expected


def test_staging_event_hour_range(duckdb_connection):
    min_hour, max_hour = duckdb_connection.execute(
        "SELECT MIN(event_hour), MAX(event_hour) FROM stg_ad_events"
    ).fetchone()
    assert 0 <= int(min_hour) <= 23
    assert 0 <= int(max_hour) <= 23


def test_staging_treatment_group_values_only_expected(duckdb_connection):
    values = {
        row[0]
        for row in duckdb_connection.execute(
            "SELECT DISTINCT treatment_group FROM stg_email_experiment"
        ).fetchall()
    }
    assert values == set(HILLSTROM_CLEAN_GROUPS)
