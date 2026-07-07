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

LOADED_TABLES = {
    "raw_avazu_ads": {
        "profile_key": "avazu",
        "cleaning_key": None,
        "row_field": "row_count",
    },
    "raw_hillstrom_email": {
        "profile_key": "hillstrom",
        "cleaning_key": None,
        "row_field": "row_count",
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
    passed = abs(float(actual_ctr) - float(expected_ctr)) <= tolerance
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
    passed = abs(float(actual_rate) - float(expected_rate)) <= tolerance
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


def validate_mart_tables_empty(
    connection: duckdb.DuckDBPyConnection,
) -> list[ValidationResult]:
    results: list[ValidationResult] = []
    for table_name in MART_TABLES:
        actual = get_table_row_count(connection, table_name)
        passed = actual == 0
        results.append(
            ValidationResult(
                check_name=f"{table_name}_empty",
                status="pass" if passed else "fail",
                expected=0,
                actual=actual,
                message=(
                    f"{table_name} remains empty before analytics marts"
                    if passed
                    else f"{table_name} should be empty but has {actual:,} rows"
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
        checks.extend(validate_mart_tables_empty(connection))
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
