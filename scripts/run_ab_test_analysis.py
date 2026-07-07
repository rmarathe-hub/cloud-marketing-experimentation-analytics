#!/usr/bin/env python3
"""Build mart_ab_test_results from stg_email_experiment."""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest

from create_duckdb_database import DatabaseConfig, _display_path, load_config
from paths import AB_TEST_SUMMARY

MART_TABLE = "mart_ab_test_results"
CONTROL_GROUP = "control"
TREATMENT_ORDER = ("control", "mens_email", "womens_email")
SIGNIFICANCE_ALPHA = 0.05

GROUP_METRICS_SQL = """
SELECT
    treatment_group,
    MAX(treatment_label) AS treatment_label,
    COUNT(*)::BIGINT AS recipients,
    SUM(converted)::BIGINT AS conversions,
    AVG(converted::DOUBLE) AS conversion_rate,
    SUM(revenue)::DOUBLE AS total_revenue,
    AVG(revenue::DOUBLE) AS revenue_per_customer
FROM stg_email_experiment
GROUP BY treatment_group
ORDER BY treatment_group
"""


def ensure_database_ready(config: DatabaseConfig) -> None:
    if not config.database_path.exists():
        raise RuntimeError(
            f"DuckDB database not found at {config.database_path}. "
            "Run create_duckdb_database.py and load_to_duckdb.py first."
        )


def ensure_staging_has_data(connection: duckdb.DuckDBPyConnection) -> int:
    row_count = int(
        connection.execute("SELECT COUNT(*) FROM stg_email_experiment").fetchone()[0]
    )
    if row_count == 0:
        raise RuntimeError(
            "stg_email_experiment is empty. Run `python scripts/load_to_duckdb.py` first."
        )
    return row_count


def clear_mart_table(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute(f"DELETE FROM {MART_TABLE}")


def fetch_group_metrics(connection: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    rows = connection.execute(GROUP_METRICS_SQL).fetchall()
    metrics: list[dict[str, Any]] = []
    for row in rows:
        metrics.append(
            {
                "treatment_group": row[0],
                "treatment_label": row[1],
                "recipients": int(row[2]),
                "conversions": int(row[3]),
                "conversion_rate": float(row[4]),
                "total_revenue": float(row[5]),
                "revenue_per_customer": float(row[6]),
            }
        )
    return metrics


def _proportion_diff_ci(
    treatment_rate: float,
    treatment_n: int,
    control_rate: float,
    control_n: int,
    alpha: float = SIGNIFICANCE_ALPHA,
) -> tuple[float, float]:
    diff = treatment_rate - control_rate
    if treatment_n == 0 or control_n == 0:
        return diff, diff
    se = math.sqrt(
        (treatment_rate * (1 - treatment_rate) / treatment_n)
        + (control_rate * (1 - control_rate) / control_n)
    )
    z_value = stats.norm.ppf(1 - alpha / 2)
    margin = z_value * se
    return diff - margin, diff + margin


def _two_proportion_pvalue(
    treatment_conversions: int,
    treatment_recipients: int,
    control_conversions: int,
    control_recipients: int,
) -> float:
    if treatment_recipients == 0 or control_recipients == 0:
        return 1.0
    count = [treatment_conversions, control_conversions]
    nobs = [treatment_recipients, control_recipients]
    _, p_value = proportions_ztest(count, nobs)
    return float(p_value)


def build_ab_test_rows(group_metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    metrics_by_group = {row["treatment_group"]: row for row in group_metrics}
    if CONTROL_GROUP not in metrics_by_group:
        raise RuntimeError(f"Missing required control group: {CONTROL_GROUP}")

    control = metrics_by_group[CONTROL_GROUP]
    control_rate = control["conversion_rate"]
    control_revenue_per_customer = control["revenue_per_customer"]

    results: list[dict[str, Any]] = []
    for group_name in TREATMENT_ORDER:
        if group_name not in metrics_by_group:
            continue
        group = metrics_by_group[group_name]
        if group_name == CONTROL_GROUP:
            results.append(
                {
                    **group,
                    "control_conversion_rate": control_rate,
                    "absolute_lift": 0.0,
                    "relative_lift_pct": 0.0,
                    "incremental_revenue": 0.0,
                    "p_value": None,
                    "ci_lower": 0.0,
                    "ci_upper": 0.0,
                    "statistically_significant": False,
                }
            )
            continue

        absolute_lift = group["conversion_rate"] - control_rate
        relative_lift_pct = (
            0.0
            if control_rate == 0
            else (absolute_lift / control_rate) * 100.0
        )
        incremental_revenue = (
            group["revenue_per_customer"] - control_revenue_per_customer
        ) * group["recipients"]
        p_value = _two_proportion_pvalue(
            group["conversions"],
            group["recipients"],
            control["conversions"],
            control["recipients"],
        )
        ci_lower, ci_upper = _proportion_diff_ci(
            group["conversion_rate"],
            group["recipients"],
            control_rate,
            control["recipients"],
        )
        results.append(
            {
                **group,
                "control_conversion_rate": control_rate,
                "absolute_lift": absolute_lift,
                "relative_lift_pct": relative_lift_pct,
                "incremental_revenue": incremental_revenue,
                "p_value": p_value,
                "ci_lower": ci_lower,
                "ci_upper": ci_upper,
                "statistically_significant": p_value < SIGNIFICANCE_ALPHA,
            }
        )
    return results


def insert_ab_test_rows(
    connection: duckdb.DuckDBPyConnection,
    rows: list[dict[str, Any]],
) -> None:
    for row in rows:
        connection.execute(
            f"""
            INSERT INTO {MART_TABLE} (
                treatment_group,
                treatment_label,
                recipients,
                conversions,
                conversion_rate,
                total_revenue,
                revenue_per_customer,
                control_conversion_rate,
                absolute_lift,
                relative_lift_pct,
                incremental_revenue,
                p_value,
                ci_lower,
                ci_upper,
                statistically_significant
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                row["treatment_group"],
                row["treatment_label"],
                row["recipients"],
                row["conversions"],
                row["conversion_rate"],
                row["total_revenue"],
                row["revenue_per_customer"],
                row["control_conversion_rate"],
                row["absolute_lift"],
                row["relative_lift_pct"],
                row["incremental_revenue"],
                row["p_value"],
                row["ci_lower"],
                row["ci_upper"],
                row["statistically_significant"],
            ],
        )


def build_summary(
    config: DatabaseConfig,
    staging_rows: int,
    ab_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    serializable_rows = []
    for row in ab_rows:
        serializable_rows.append(
            {
                **row,
                "conversion_rate": round(row["conversion_rate"], 6),
                "total_revenue": round(row["total_revenue"], 2),
                "revenue_per_customer": round(row["revenue_per_customer"], 6),
                "control_conversion_rate": round(row["control_conversion_rate"], 6),
                "absolute_lift": round(row["absolute_lift"], 6),
                "relative_lift_pct": round(row["relative_lift_pct"], 4),
                "incremental_revenue": round(row["incremental_revenue"], 2),
                "p_value": None if row["p_value"] is None else round(row["p_value"], 6),
                "ci_lower": round(row["ci_lower"], 6),
                "ci_upper": round(row["ci_upper"], 6),
            }
        )

    total_recipients = sum(row["recipients"] for row in ab_rows)
    significant_treatments = [
        row["treatment_group"]
        for row in serializable_rows
        if row["treatment_group"] != CONTROL_GROUP and row["statistically_significant"]
    ]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database_path": _display_path(config.database_path),
        "source_table": "stg_email_experiment",
        "mart_table": MART_TABLE,
        "staging_row_count": staging_rows,
        "mart_row_count": len(ab_rows),
        "total_recipients": total_recipients,
        "significance_alpha": SIGNIFICANCE_ALPHA,
        "significant_treatments": significant_treatments,
        "results": serializable_rows,
        "success": len(ab_rows) > 0 and total_recipients == staging_rows,
    }


def write_ab_test_summary(summary: dict[str, Any], path: Path | None = None) -> Path:
    output_path = path or AB_TEST_SUMMARY
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2))
    return output_path


def run_ab_test_analysis(
    config: DatabaseConfig | None = None,
    summary_path: Path | None = None,
) -> dict[str, Any]:
    config = config or load_config()
    ensure_database_ready(config)

    connection = duckdb.connect(str(config.database_path))
    try:
        staging_rows = ensure_staging_has_data(connection)
        clear_mart_table(connection)
        group_metrics = fetch_group_metrics(connection)
        ab_rows = build_ab_test_rows(group_metrics)
        insert_ab_test_rows(connection, ab_rows)
    finally:
        connection.close()

    summary = build_summary(config, staging_rows, ab_rows)
    write_ab_test_summary(summary, summary_path)
    return summary


def main() -> int:
    print("=" * 60)
    print("A/B test analysis mart build")
    print("=" * 60)

    try:
        config = load_config()
        summary = run_ab_test_analysis(config)

        print(f"Database: {config.database_path}")
        print(f"Source:   stg_email_experiment ({summary['staging_row_count']:,} rows)")
        print(f"Mart:     {MART_TABLE} ({summary['mart_row_count']:,} treatment rows)")
        print()
        for row in summary["results"]:
            significance = (
                "n/a"
                if row["p_value"] is None
                else f"p={row['p_value']:.4f}"
            )
            print(
                f"  {row['treatment_label']}: "
                f"{row['recipients']:,} recipients, "
                f"conversion {row['conversion_rate']:.4%}, "
                f"lift {row['absolute_lift']:.4%}, "
                f"{significance}"
            )
        print()
        if summary["significant_treatments"]:
            print(
                "Significant treatments: "
                + ", ".join(summary["significant_treatments"])
            )
        else:
            print("No treatments statistically significant at alpha 0.05.")
        print(f"Summary written to {AB_TEST_SUMMARY}")

        if not summary["success"]:
            print("A/B test mart build did not reconcile with staging rows.", file=sys.stderr)
            return 1
        return 0

    except RuntimeError as exc:
        print(f"A/B test analysis failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
