#!/usr/bin/env python3
"""Validate DuckDB loads against profiling and cleaning summaries."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb

from create_duckdb_database import EXPECTED_TABLES, DatabaseConfig, _display_path, load_config
from paths import (
    CLEANING_SUMMARY,
    DATA_VALIDATION_SUMMARY,
    RAW_PROFILE_SUMMARY,
)

MART_TABLES = tuple(
    table_name for table_name, layer in EXPECTED_TABLES.items() if layer == "mart"
)

POPULATED_MART_TABLES = (
    "mart_campaign_kpis",
    "mart_ctr_trends",
    "mart_device_app_performance",
    "mart_ab_test_results",
    "mart_forecast_inputs",
    "mart_forecast_results",
)

PENDING_MART_TABLES = tuple(
    table_name for table_name in MART_TABLES if table_name not in POPULATED_MART_TABLES
)

LOADED_TABLES = {
    "raw_avazu_ads": {
        "profile_key": None,
        "cleaning_key": "avazu",
        "row_field": "input_rows",
    },
    "raw_hillstrom_email": {
        "profile_key": None,
        "cleaning_key": "hillstrom",
        "row_field": "input_rows",
    },
    "stg_ad_events": {
        "profile_key": None,
        "cleaning_key": "avazu",
        "row_field": "output_rows",
    },
    "stg_email_experiment": {
        "profile_key": None,
        "cleaning_key": "hillstrom",
        "row_field": "output_rows",
    },
}


@dataclass(frozen=True)
class ValidationResult:
    check_name: str
    status: str
    expected: Any
    actual: Any
    message: str


def load_json_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing summary file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_expectations(
    profile_path: Path | None = None,
    cleaning_path: Path | None = None,
) -> dict[str, Any]:
    profile = load_json_summary(profile_path or RAW_PROFILE_SUMMARY)
    cleaning = load_json_summary(cleaning_path or CLEANING_SUMMARY)
    return {
        "profile": profile["datasets"],
        "cleaning": cleaning["datasets"],
    }


def get_table_row_count(connection: duckdb.DuckDBPyConnection, table_name: str) -> int:
    return int(connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0])


def validate_row_counts(
    connection: duckdb.DuckDBPyConnection,
    expectations: dict[str, Any],
) -> list[ValidationResult]:
    results: list[ValidationResult] = []

    for table_name, mapping in LOADED_TABLES.items():
        actual = get_table_row_count(connection, table_name)
        expected = None

        if mapping["profile_key"]:
            expected = expectations["profile"][mapping["profile_key"]][mapping["row_field"]]
        elif mapping["cleaning_key"]:
            expected = expectations["cleaning"][mapping["cleaning_key"]][mapping["row_field"]]

        passed = actual == expected
        results.append(
            ValidationResult(
                check_name=f"{table_name}_row_count",
                status="pass" if passed else "fail",
                expected=expected,
                actual=actual,
                message=(
                    f"{table_name} row count matches expected {expected:,}"
                    if passed
                    else f"{table_name} row count {actual:,} != expected {expected:,}"
                ),
            )
        )

    return results


def validate_avazu_ctr(
    connection: duckdb.DuckDBPyConnection,
    expectations: dict[str, Any],
    tolerance: float = 0.0001,
) -> ValidationResult:
    expected_ctr = expectations["cleaning"]["avazu"]["ctr"]
    actual_ctr = connection.execute(
        "SELECT AVG(CAST(click AS DOUBLE)) FROM stg_ad_events"
    ).fetchone()[0]
    actual_ctr = 0.0 if actual_ctr is None else float(actual_ctr)
    passed = abs(actual_ctr - float(expected_ctr)) <= tolerance
    return ValidationResult(
        check_name="stg_ad_events_ctr",
        status="pass" if passed else "fail",
        expected=expected_ctr,
        actual=round(float(actual_ctr), 6),
        message=(
            f"Avazu CTR matches cleaning summary ({expected_ctr:.6f})"
            if passed
            else f"Avazu CTR {actual_ctr:.6f} != expected {expected_ctr:.6f}"
        ),
    )


def validate_hillstrom_visit_rate(
    connection: duckdb.DuckDBPyConnection,
    expectations: dict[str, Any],
    tolerance: float = 0.0001,
) -> ValidationResult:
    expected_rate = expectations["cleaning"]["hillstrom"]["visit_rate"]
    actual_rate = connection.execute(
        "SELECT AVG(CAST(visit AS DOUBLE)) FROM stg_email_experiment"
    ).fetchone()[0]
    actual_rate = 0.0 if actual_rate is None else float(actual_rate)
    passed = abs(actual_rate - float(expected_rate)) <= tolerance
    return ValidationResult(
        check_name="stg_email_experiment_visit_rate",
        status="pass" if passed else "fail",
        expected=expected_rate,
        actual=round(float(actual_rate), 6),
        message=(
            f"Hillstrom visit rate matches cleaning summary ({expected_rate:.6f})"
            if passed
            else (
                f"Hillstrom visit rate {actual_rate:.6f} != expected "
                f"{expected_rate:.6f}"
            )
        ),
    )


def validate_pending_mart_tables_empty(
    connection: duckdb.DuckDBPyConnection,
) -> list[ValidationResult]:
    results: list[ValidationResult] = []
    for table_name in PENDING_MART_TABLES:
        actual = get_table_row_count(connection, table_name)
        passed = actual == 0
        results.append(
            ValidationResult(
                check_name=f"{table_name}_empty",
                status="pass" if passed else "fail",
                expected=0,
                actual=actual,
                message=(
                    f"{table_name} remains empty before its analytics script runs"
                    if passed
                    else f"{table_name} should be empty but has {actual:,} rows"
                ),
            )
        )
    return results


def validate_campaign_kpi_mart(
    connection: duckdb.DuckDBPyConnection,
    expectations: dict[str, Any],
    tolerance: float = 0.0001,
) -> list[ValidationResult]:
    results: list[ValidationResult] = []
    row_count = get_table_row_count(connection, "mart_campaign_kpis")
    populated = row_count > 0
    results.append(
        ValidationResult(
            check_name="mart_campaign_kpis_populated",
            status="pass" if populated else "fail",
            expected="> 0",
            actual=row_count,
            message=(
                f"mart_campaign_kpis has {row_count:,} daily KPI row(s)"
                if populated
                else "mart_campaign_kpis is empty; run run_campaign_kpis.py"
            ),
        )
    )

    expected_ctr = expectations["cleaning"]["avazu"]["ctr"]
    actual_ctr = connection.execute(
        """
        SELECT CASE
            WHEN SUM(impressions) = 0 THEN 0.0
            ELSE SUM(clicks)::DOUBLE / SUM(impressions)::DOUBLE
        END
        FROM mart_campaign_kpis
        """
    ).fetchone()[0]
    actual_ctr = 0.0 if actual_ctr is None else float(actual_ctr)
    ctr_passed = populated and abs(actual_ctr - float(expected_ctr)) <= tolerance
    results.append(
        ValidationResult(
            check_name="mart_campaign_kpis_ctr",
            status="pass" if ctr_passed else "fail",
            expected=expected_ctr,
            actual=round(actual_ctr, 6),
            message=(
                f"Campaign KPI CTR matches cleaning summary ({expected_ctr:.6f})"
                if ctr_passed
                else (
                    f"Campaign KPI CTR {actual_ctr:.6f} != expected {expected_ctr:.6f}"
                    if populated
                    else "Campaign KPI CTR unavailable because mart is empty"
                )
            ),
        )
    )
    return results


def validate_funnel_segment_marts(
    connection: duckdb.DuckDBPyConnection,
    expectations: dict[str, Any],
    tolerance: float = 0.0001,
) -> list[ValidationResult]:
    results: list[ValidationResult] = []
    expected_staging_rows = expectations["cleaning"]["avazu"]["output_rows"]
    expected_ctr = expectations["cleaning"]["avazu"]["ctr"]

    ctr_trends_count = get_table_row_count(connection, "mart_ctr_trends")
    ctr_populated = ctr_trends_count > 0
    results.append(
        ValidationResult(
            check_name="mart_ctr_trends_populated",
            status="pass" if ctr_populated else "fail",
            expected="> 0",
            actual=ctr_trends_count,
            message=(
                f"mart_ctr_trends has {ctr_trends_count:,} hourly row(s)"
                if ctr_populated
                else "mart_ctr_trends is empty; run run_funnel_segment_analysis.py"
            ),
        )
    )

    ctr_trend_impressions = connection.execute(
        "SELECT COALESCE(SUM(impressions), 0) FROM mart_ctr_trends"
    ).fetchone()[0]
    impressions_match = ctr_populated and int(ctr_trend_impressions) == int(expected_staging_rows)
    results.append(
        ValidationResult(
            check_name="mart_ctr_trends_impressions",
            status="pass" if impressions_match else "fail",
            expected=expected_staging_rows,
            actual=int(ctr_trend_impressions),
            message=(
                "mart_ctr_trends impressions reconcile with staging rows"
                if impressions_match
                else (
                    "mart_ctr_trends impressions do not reconcile with staging rows"
                    if ctr_populated
                    else "mart_ctr_trends impressions unavailable because mart is empty"
                )
            ),
        )
    )

    actual_ctr = connection.execute(
        """
        SELECT CASE
            WHEN SUM(impressions) = 0 THEN 0.0
            ELSE SUM(clicks)::DOUBLE / SUM(impressions)::DOUBLE
        END
        FROM mart_ctr_trends
        """
    ).fetchone()[0]
    actual_ctr = 0.0 if actual_ctr is None else float(actual_ctr)
    ctr_passed = ctr_populated and abs(actual_ctr - float(expected_ctr)) <= tolerance
    results.append(
        ValidationResult(
            check_name="mart_ctr_trends_ctr",
            status="pass" if ctr_passed else "fail",
            expected=expected_ctr,
            actual=round(actual_ctr, 6),
            message=(
                f"Hourly trend CTR matches cleaning summary ({expected_ctr:.6f})"
                if ctr_passed
                else (
                    f"Hourly trend CTR {actual_ctr:.6f} != expected {expected_ctr:.6f}"
                    if ctr_populated
                    else "Hourly trend CTR unavailable because mart is empty"
                )
            ),
        )
    )

    device_count = get_table_row_count(connection, "mart_device_app_performance")
    device_populated = device_count > 0
    results.append(
        ValidationResult(
            check_name="mart_device_app_performance_populated",
            status="pass" if device_populated else "fail",
            expected="> 0",
            actual=device_count,
            message=(
                f"mart_device_app_performance has {device_count:,} segment row(s)"
                if device_populated
                else (
                    "mart_device_app_performance is empty; "
                    "run run_funnel_segment_analysis.py"
                )
            ),
        )
    )

    device_impressions = connection.execute(
        "SELECT COALESCE(SUM(impressions), 0) FROM mart_device_app_performance"
    ).fetchone()[0]
    device_impressions_match = (
        device_populated and int(device_impressions) == int(expected_staging_rows)
    )
    results.append(
        ValidationResult(
            check_name="mart_device_app_performance_impressions",
            status="pass" if device_impressions_match else "fail",
            expected=expected_staging_rows,
            actual=int(device_impressions),
            message=(
                "mart_device_app_performance impressions reconcile with staging rows"
                if device_impressions_match
                else (
                    "mart_device_app_performance impressions do not reconcile "
                    "with staging rows"
                    if device_populated
                    else (
                        "mart_device_app_performance impressions unavailable "
                        "because mart is empty"
                    )
                )
            ),
        )
    )

    click_share_sum = connection.execute(
        "SELECT COALESCE(SUM(click_share), 0.0) FROM mart_device_app_performance"
    ).fetchone()[0]
    click_share_sum = 0.0 if click_share_sum is None else float(click_share_sum)
    share_passed = device_populated and abs(click_share_sum - 1.0) <= tolerance
    results.append(
        ValidationResult(
            check_name="mart_device_app_performance_click_share",
            status="pass" if share_passed else "fail",
            expected=1.0,
            actual=round(click_share_sum, 6),
            message=(
                "Segment click_share values sum to 1.0"
                if share_passed
                else (
                    f"Segment click_share sum {click_share_sum:.6f} != 1.0"
                    if device_populated
                    else "Segment click_share unavailable because mart is empty"
                )
            ),
        )
    )
    return results


def validate_ab_test_mart(
    connection: duckdb.DuckDBPyConnection,
    expectations: dict[str, Any],
    tolerance: float = 0.0001,
) -> list[ValidationResult]:
    results: list[ValidationResult] = []
    expected_counts = expectations["cleaning"]["hillstrom"]["treatment_group_counts"]
    expected_visit_rate = expectations["cleaning"]["hillstrom"]["visit_rate"]
    expected_hillstrom_rows = expectations["cleaning"]["hillstrom"]["output_rows"]

    row_count = get_table_row_count(connection, "mart_ab_test_results")
    populated = row_count == len(expected_counts)
    results.append(
        ValidationResult(
            check_name="mart_ab_test_results_populated",
            status="pass" if populated else "fail",
            expected=len(expected_counts),
            actual=row_count,
            message=(
                f"mart_ab_test_results has {row_count:,} treatment row(s)"
                if populated
                else "mart_ab_test_results is empty or incomplete; run run_ab_test_analysis.py"
            ),
        )
    )

    mart_counts_rows = connection.execute(
        """
        SELECT treatment_group, recipients
        FROM mart_ab_test_results
        ORDER BY treatment_group
        """
    ).fetchall()
    actual_counts = {row[0]: int(row[1]) for row in mart_counts_rows}
    counts_match = populated and actual_counts == expected_counts
    results.append(
        ValidationResult(
            check_name="mart_ab_test_results_group_counts",
            status="pass" if counts_match else "fail",
            expected=expected_counts,
            actual=actual_counts,
            message=(
                "A/B mart treatment group counts match cleaning summary"
                if counts_match
                else "A/B mart treatment group counts do not match cleaning summary"
            ),
        )
    )

    total_recipients = sum(actual_counts.values()) if populated else 0
    recipients_match = populated and total_recipients == int(expected_hillstrom_rows)
    results.append(
        ValidationResult(
            check_name="mart_ab_test_results_recipients",
            status="pass" if recipients_match else "fail",
            expected=expected_hillstrom_rows,
            actual=total_recipients,
            message=(
                "A/B mart recipients reconcile with Hillstrom staging rows"
                if recipients_match
                else "A/B mart recipients do not reconcile with Hillstrom staging rows"
            ),
        )
    )

    weighted_rate = connection.execute(
        """
        SELECT CASE
            WHEN SUM(recipients) = 0 THEN 0.0
            ELSE SUM(conversions)::DOUBLE / SUM(recipients)::DOUBLE
        END
        FROM mart_ab_test_results
        """
    ).fetchone()[0]
    weighted_rate = None if weighted_rate is None else float(weighted_rate)
    rate_match = (
        populated
        and weighted_rate is not None
        and abs(weighted_rate - float(expected_visit_rate)) <= tolerance
    )
    results.append(
        ValidationResult(
            check_name="mart_ab_test_results_overall_conversion_rate",
            status="pass" if rate_match else "fail",
            expected=expected_visit_rate,
            actual=round(weighted_rate, 6) if weighted_rate is not None else None,
            message=(
                "A/B mart weighted conversion rate matches Hillstrom visit rate"
                if rate_match
                else "A/B mart weighted conversion rate does not match Hillstrom visit rate"
            ),
        )
    )

    treatment_p_values = connection.execute(
        """
        SELECT COUNT(*)
        FROM mart_ab_test_results
        WHERE treatment_group != 'control' AND p_value IS NOT NULL
        """
    ).fetchone()[0]
    expected_treatment_rows = len(expected_counts) - 1
    significance_ready = populated and int(treatment_p_values) == expected_treatment_rows
    results.append(
        ValidationResult(
            check_name="mart_ab_test_results_treatment_significance",
            status="pass" if significance_ready else "fail",
            expected=expected_treatment_rows,
            actual=int(treatment_p_values),
            message=(
                "Treatment rows include significance test outputs"
                if significance_ready
                else "Treatment rows missing significance test outputs"
            ),
        )
    )
    return results


def validate_forecast_marts(
    connection: duckdb.DuckDBPyConnection,
    expectations: dict[str, Any],
    tolerance: float = 0.0001,
) -> list[ValidationResult]:
    results: list[ValidationResult] = []
    expected_staging_rows = expectations["cleaning"]["avazu"]["output_rows"]
    expected_ctr = expectations["cleaning"]["avazu"]["ctr"]

    inputs_count = get_table_row_count(connection, "mart_forecast_inputs")
    inputs_populated = inputs_count > 0
    results.append(
        ValidationResult(
            check_name="mart_forecast_inputs_populated",
            status="pass" if inputs_populated else "fail",
            expected="> 0",
            actual=inputs_count,
            message=(
                f"mart_forecast_inputs has {inputs_count:,} hourly row(s)"
                if inputs_populated
                else "mart_forecast_inputs is empty; run run_ctr_forecast.py"
            ),
        )
    )

    input_impressions = connection.execute(
        "SELECT COALESCE(SUM(impressions), 0) FROM mart_forecast_inputs"
    ).fetchone()[0]
    impressions_match = inputs_populated and int(input_impressions) == int(expected_staging_rows)
    results.append(
        ValidationResult(
            check_name="mart_forecast_inputs_impressions",
            status="pass" if impressions_match else "fail",
            expected=expected_staging_rows,
            actual=int(input_impressions),
            message=(
                "mart_forecast_inputs impressions reconcile with staging rows"
                if impressions_match
                else "mart_forecast_inputs impressions do not reconcile with staging rows"
            ),
        )
    )

    actual_ctr = connection.execute(
        """
        SELECT CASE
            WHEN SUM(impressions) = 0 THEN 0.0
            ELSE SUM(clicks)::DOUBLE / SUM(impressions)::DOUBLE
        END
        FROM mart_forecast_inputs
        """
    ).fetchone()[0]
    actual_ctr = 0.0 if actual_ctr is None else float(actual_ctr)
    ctr_passed = inputs_populated and abs(actual_ctr - float(expected_ctr)) <= tolerance
    results.append(
        ValidationResult(
            check_name="mart_forecast_inputs_ctr",
            status="pass" if ctr_passed else "fail",
            expected=expected_ctr,
            actual=round(actual_ctr, 6),
            message=(
                f"Forecast input CTR matches cleaning summary ({expected_ctr:.6f})"
                if ctr_passed
                else "Forecast input CTR does not match cleaning summary"
            ),
        )
    )

    results_count = get_table_row_count(connection, "mart_forecast_results")
    results_populated = results_count > 0
    results.append(
        ValidationResult(
            check_name="mart_forecast_results_populated",
            status="pass" if results_populated else "fail",
            expected="> 0",
            actual=results_count,
            message=(
                f"mart_forecast_results has {results_count:,} holdout row(s)"
                if results_populated
                else "mart_forecast_results is empty; run run_ctr_forecast.py"
            ),
        )
    )

    metric_rows = connection.execute(
        """
        SELECT COUNT(*)
        FROM mart_forecast_results
        WHERE mae IS NOT NULL AND rmse IS NOT NULL AND model_name IS NOT NULL
        """
    ).fetchone()[0]
    metrics_ready = results_populated and int(metric_rows) == results_count
    results.append(
        ValidationResult(
            check_name="mart_forecast_results_metrics",
            status="pass" if metrics_ready else "fail",
            expected=results_count,
            actual=int(metric_rows),
            message=(
                "Forecast results include model metrics and model name"
                if metrics_ready
                else "Forecast results missing model metrics or model name"
            ),
        )
    )
    return results


def validate_treatment_groups(
    connection: duckdb.DuckDBPyConnection,
    expectations: dict[str, Any],
) -> ValidationResult:
    expected_counts = expectations["cleaning"]["hillstrom"]["treatment_group_counts"]
    rows = connection.execute(
        """
        SELECT treatment_group, COUNT(*) AS recipients
        FROM stg_email_experiment
        GROUP BY treatment_group
        ORDER BY treatment_group
        """
    ).fetchall()
    actual_counts = {row[0]: int(row[1]) for row in rows}
    passed = actual_counts == expected_counts
    return ValidationResult(
        check_name="stg_email_experiment_treatment_groups",
        status="pass" if passed else "fail",
        expected=expected_counts,
        actual=actual_counts,
        message=(
            "Hillstrom treatment group counts match cleaning summary"
            if passed
            else "Hillstrom treatment group counts do not match cleaning summary"
        ),
    )


def run_validation(
    config: DatabaseConfig | None = None,
    expectations: dict[str, Any] | None = None,
    summary_path: Path | None = None,
) -> dict[str, Any]:
    config = config or load_config()
    expectations = expectations or load_expectations()

    if not config.database_path.exists():
        raise RuntimeError(
            f"DuckDB database not found at {config.database_path}. "
            "Run create and load scripts first."
        )

    connection = duckdb.connect(str(config.database_path), read_only=True)
    try:
        checks: list[ValidationResult] = []
        checks.extend(validate_row_counts(connection, expectations))
        checks.append(validate_avazu_ctr(connection, expectations))
        checks.append(validate_hillstrom_visit_rate(connection, expectations))
        checks.append(validate_treatment_groups(connection, expectations))
        checks.extend(validate_campaign_kpi_mart(connection, expectations))
        checks.extend(validate_funnel_segment_marts(connection, expectations))
        checks.extend(validate_ab_test_mart(connection, expectations))
        checks.extend(validate_forecast_marts(connection, expectations))
        checks.extend(validate_pending_mart_tables_empty(connection))
    finally:
        connection.close()

    failed = [check for check in checks if check.status != "pass"]
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database_path": _display_path(config.database_path),
        "checks": [
            {
                "check_name": check.check_name,
                "status": check.status,
                "expected": check.expected,
                "actual": check.actual,
                "message": check.message,
            }
            for check in checks
        ],
        "passed_count": sum(1 for check in checks if check.status == "pass"),
        "failed_count": len(failed),
        "success": len(failed) == 0,
    }
    write_validation_summary(summary, summary_path)
    return summary


def write_validation_summary(summary: dict[str, Any], path: Path | None = None) -> Path:
    output_path = path or DATA_VALIDATION_SUMMARY
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2))
    return output_path


def main() -> int:
    print("=" * 60)
    print("DuckDB data validation")
    print("=" * 60)

    try:
        config = load_config()
        summary = run_validation(config)

        print(f"Database: {config.database_path}")
        print()
        for check in summary["checks"]:
            status = "✓" if check["status"] == "pass" else "✗"
            print(f"{status} {check['message']}")

        print()
        print(
            f"Passed {summary['passed_count']} of "
            f"{summary['passed_count'] + summary['failed_count']} checks."
        )
        print(f"Summary written to {DATA_VALIDATION_SUMMARY}")

        if not summary["success"]:
            return 1
        return 0

    except (FileNotFoundError, RuntimeError) as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
