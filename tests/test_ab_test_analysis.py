"""run_ab_test_analysis.py tests for Day 10 Hillstrom A/B mart."""

from __future__ import annotations

import json

import duckdb
import pandas as pd
import pytest
from statsmodels.stats.proportion import proportions_ztest

import create_duckdb_database as db_setup
import load_to_duckdb as loader
import run_ab_test_analysis as ab_test
import validate_data as validator
from clean_hillstrom_email import clean_hillstrom_email
from helpers import (
    DUCKDB_MART_TABLES_PENDING,
    DUCKDB_MART_TABLES_POPULATED,
    HILLSTROM_CLEAN_GROUPS,
    WEEK1_LOCKED,
    assert_approx_ratio,
    run_implemented_week2_analytics,
    tiny_hillstrom_dataframe,
    write_tiny_hillstrom_csv,
)
from paths import SQL_DIR

pytestmark = [pytest.mark.unit, pytest.mark.duckdb]


def _build_tiny_hillstrom_bundle(tmp_path):
    raw_dir = tmp_path / "raw"
    processed = tmp_path / "processed"
    raw_dir.mkdir(parents=True)
    processed.mkdir(parents=True)

    hillstrom_raw = write_tiny_hillstrom_csv(raw_dir / "hillstrom_email.csv")
    hillstrom_df = pd.read_csv(hillstrom_raw)
    hillstrom_clean, hillstrom_summary = clean_hillstrom_email(hillstrom_df)
    hillstrom_parquet = processed / "hillstrom_clean.parquet"
    hillstrom_clean.to_parquet(hillstrom_parquet, index=False)

    db_path = processed / "marketing_analytics.duckdb"
    config = db_setup.DatabaseConfig(database_path=db_path)
    db_setup.create_database(config=config, sql_dir=SQL_DIR)

    loader.load_data(
        config=config,
        targets=[
            loader.LoadTarget(
                "stg_email_experiment", "staging", hillstrom_parquet, "parquet"
            ),
        ],
        summary_path=processed / "duckdb_load_summary.json",
    )
    return {
        "config": config,
        "processed": processed,
        "hillstrom_summary": hillstrom_summary,
        "staging_rows": len(hillstrom_clean),
    }


def test_ab_test_module_exports_main():
    assert hasattr(ab_test, "main")
    assert hasattr(ab_test, "run_ab_test_analysis")


def test_run_ab_test_analysis_populates_mart(tmp_path):
    bundle = _build_tiny_hillstrom_bundle(tmp_path)
    summary_path = bundle["processed"] / "ab_test_summary.json"

    summary = ab_test.run_ab_test_analysis(
        config=bundle["config"],
        summary_path=summary_path,
    )

    assert summary["success"] is True
    assert summary["mart_row_count"] == 3
    assert summary_path.exists()

    connection = duckdb.connect(str(bundle["config"].database_path), read_only=True)
    try:
        mart_count = connection.execute(
            "SELECT COUNT(*) FROM mart_ab_test_results"
        ).fetchone()[0]
        assert mart_count == 3
        for table_name in DUCKDB_MART_TABLES_PENDING:
            pending_count = connection.execute(
                f"SELECT COUNT(*) FROM {table_name}"
            ).fetchone()[0]
            assert pending_count == 0
    finally:
        connection.close()


def test_control_row_has_zero_lift(tmp_path):
    bundle = _build_tiny_hillstrom_bundle(tmp_path)
    ab_test.run_ab_test_analysis(
        config=bundle["config"],
        summary_path=bundle["processed"] / "ab_test_summary.json",
    )

    connection = duckdb.connect(str(bundle["config"].database_path), read_only=True)
    try:
        row = connection.execute(
            """
            SELECT absolute_lift, relative_lift_pct, p_value, statistically_significant
            FROM mart_ab_test_results
            WHERE treatment_group = 'control'
            """
        ).fetchone()
    finally:
        connection.close()

    assert float(row[0]) == 0.0
    assert float(row[1]) == 0.0
    assert row[2] is None
    assert row[3] is False


def test_treatment_p_value_matches_statsmodels(tmp_path):
    bundle = _build_tiny_hillstrom_bundle(tmp_path)
    summary = ab_test.run_ab_test_analysis(
        config=bundle["config"],
        summary_path=bundle["processed"] / "ab_test_summary.json",
    )

    connection = duckdb.connect(str(bundle["config"].database_path), read_only=True)
    try:
        control = connection.execute(
            """
            SELECT conversions, recipients
            FROM mart_ab_test_results
            WHERE treatment_group = 'control'
            """
        ).fetchone()
        treatment = connection.execute(
            """
            SELECT treatment_group, conversions, recipients, p_value
            FROM mart_ab_test_results
            WHERE treatment_group = 'mens_email'
            """
        ).fetchone()
    finally:
        connection.close()

    _, expected_p = proportions_ztest(
        [int(treatment[1]), int(control[0])],
        [int(treatment[2]), int(control[1])],
    )
    assert_approx_ratio(float(treatment[3]), float(expected_p))
    assert summary["results"]


def test_run_ab_test_analysis_is_idempotent(tmp_path):
    bundle = _build_tiny_hillstrom_bundle(tmp_path)
    summary_path = bundle["processed"] / "ab_test_summary.json"

    first = ab_test.run_ab_test_analysis(config=bundle["config"], summary_path=summary_path)
    second = ab_test.run_ab_test_analysis(config=bundle["config"], summary_path=summary_path)

    assert first["results"] == second["results"]


def test_ab_test_summary_schema(tmp_path):
    bundle = _build_tiny_hillstrom_bundle(tmp_path)
    summary_path = bundle["processed"] / "ab_test_summary.json"
    ab_test.run_ab_test_analysis(config=bundle["config"], summary_path=summary_path)

    payload = json.loads(summary_path.read_text())
    for key in [
        "generated_at",
        "mart_row_count",
        "significance_alpha",
        "significant_treatments",
        "results",
        "success",
    ]:
        assert key in payload
    assert payload["mart_table"] == "mart_ab_test_results"


def test_validation_passes_after_ab_test_mart(tmp_path):
    from clean_avazu_ads import clean_avazu_ads
    from helpers import tiny_avazu_dataframe, tiny_hillstrom_dataframe

    raw_dir = tmp_path / "data" / "raw"
    processed = tmp_path / "data" / "processed"
    raw_dir.mkdir(parents=True)
    processed.mkdir(parents=True)

    avazu_raw = raw_dir / "avazu_train.csv"
    hillstrom_raw = raw_dir / "hillstrom_email.csv"
    tiny_avazu_dataframe().to_csv(avazu_raw, index=False)
    tiny_hillstrom_dataframe().to_csv(hillstrom_raw, index=False)

    avazu_clean, avazu_summary = clean_avazu_ads(pd.read_csv(avazu_raw))
    hillstrom_clean, hillstrom_summary = clean_hillstrom_email(pd.read_csv(hillstrom_raw))
    avazu_parquet = processed / "avazu_clean.parquet"
    hillstrom_parquet = processed / "hillstrom_clean.parquet"
    avazu_clean.to_parquet(avazu_parquet, index=False)
    hillstrom_clean.to_parquet(hillstrom_parquet, index=False)

    config = db_setup.DatabaseConfig(database_path=processed / "marketing_analytics.duckdb")
    db_setup.create_database(config=config, sql_dir=SQL_DIR)
    loader.load_data(
        config=config,
        targets=loader.get_load_targets(
            avazu_raw=avazu_raw,
            hillstrom_raw=hillstrom_raw,
            avazu_clean=avazu_parquet,
            hillstrom_clean=hillstrom_parquet,
        ),
        summary_path=processed / "duckdb_load_summary.json",
    )
    run_implemented_week2_analytics(config, processed)

    expectations = {
        "profile": {
            "avazu": {"row_count": len(avazu_clean)},
            "hillstrom": {"row_count": len(hillstrom_clean)},
        },
        "cleaning": {
            "avazu": {
                "input_rows": len(avazu_clean),
                "output_rows": len(avazu_clean),
                "ctr": avazu_summary["ctr"],
            },
            "hillstrom": {
                "input_rows": len(hillstrom_clean),
                "output_rows": len(hillstrom_clean),
                "visit_rate": hillstrom_summary["visit_rate"],
                "treatment_group_counts": hillstrom_summary["treatment_group_counts"],
            },
        },
    }
    validation_summary = validator.run_validation(
        config=config,
        expectations=expectations,
        summary_path=processed / "data_validation_summary.json",
    )

    ab_checks = {
        check["check_name"]: check
        for check in validation_summary["checks"]
        if check["check_name"].startswith("mart_ab_test_results")
    }
    assert ab_checks["mart_ab_test_results_populated"]["status"] == "pass"
    assert ab_checks["mart_ab_test_results_group_counts"]["status"] == "pass"
    assert ab_checks["mart_ab_test_results_treatment_significance"]["status"] == "pass"


@pytest.mark.data
@pytest.mark.slow
def test_real_ab_test_mart_matches_lock():
    from helpers import local_duckdb_available

    if not local_duckdb_available():
        pytest.skip("Local DuckDB database not present")

    from paths import DUCKDB_DEFAULT_PATH

    connection = duckdb.connect(str(DUCKDB_DEFAULT_PATH), read_only=True)
    try:
        row_count = connection.execute(
            "SELECT COUNT(*) FROM mart_ab_test_results"
        ).fetchone()[0]
        if row_count == 0:
            pytest.skip("mart_ab_test_results not populated; run run_ab_test_analysis.py")

        counts = {
            row[0]: int(row[1])
            for row in connection.execute(
                """
                SELECT treatment_group, recipients
                FROM mart_ab_test_results
                ORDER BY treatment_group
                """
            ).fetchall()
        }
        control_rate = connection.execute(
            """
            SELECT SUM(conversions)::DOUBLE / SUM(recipients)::DOUBLE
            FROM mart_ab_test_results
            """
        ).fetchone()[0]
    finally:
        connection.close()

    assert counts == HILLSTROM_CLEAN_GROUPS
    weighted_rate = connection.execute(
        """
        SELECT SUM(conversions)::DOUBLE / SUM(recipients)::DOUBLE
        FROM mart_ab_test_results
        """
    ).fetchone()[0]
    assert_approx_ratio(float(weighted_rate), WEEK1_LOCKED["hillstrom_visit_rate_ratio"])


def test_ab_test_methodology_doc_exists():
    from helpers import DOCS_DIR

    assert (DOCS_DIR / "ab_test_methodology.md").is_file()


def test_populated_mart_tables_include_ab_results():
    assert "mart_ab_test_results" in DUCKDB_MART_TABLES_POPULATED
