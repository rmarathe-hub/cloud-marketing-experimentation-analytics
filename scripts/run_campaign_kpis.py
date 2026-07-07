#!/usr/bin/env python3
"""Build mart_campaign_kpis from stg_ad_events."""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import duckdb

from create_duckdb_database import DatabaseConfig, _display_path, load_config
from paths import CAMPAIGN_KPI_SUMMARY

MART_TABLE = "mart_campaign_kpis"

CAMPAIGN_KPI_INSERT_SQL = """
INSERT INTO mart_campaign_kpis (event_date, impressions, clicks, ctr)
SELECT
    event_date,
    COUNT(*)::BIGINT AS impressions,
    SUM(click)::BIGINT AS clicks,
    CASE
        WHEN COUNT(*) = 0 THEN 0.0
        ELSE SUM(click)::DOUBLE / COUNT(*)::DOUBLE
    END AS ctr
FROM stg_ad_events
WHERE event_date IS NOT NULL
GROUP BY event_date
ORDER BY event_date
"""


def ensure_database_ready(config: DatabaseConfig) -> None:
    if not config.database_path.exists():
        raise RuntimeError(
            f"DuckDB database not found at {config.database_path}. "
            "Run create_duckdb_database.py and load_to_duckdb.py first."
        )


def ensure_staging_has_data(connection: duckdb.DuckDBPyConnection) -> int:
    row_count = int(
        connection.execute("SELECT COUNT(*) FROM stg_ad_events").fetchone()[0]
    )
    if row_count == 0:
        raise RuntimeError(
            "stg_ad_events is empty. Run `python scripts/load_to_duckdb.py` first."
        )
    return row_count


def clear_mart_table(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute(f"DELETE FROM {MART_TABLE}")


def fetch_campaign_kpis(connection: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    rows = connection.execute(
        f"""
        SELECT event_date, impressions, clicks, ctr
        FROM {MART_TABLE}
        ORDER BY event_date
        """
    ).fetchall()
    return [
        {
            "event_date": row[0].isoformat() if isinstance(row[0], date) else str(row[0]),
            "impressions": int(row[1]),
            "clicks": int(row[2]),
            "ctr": round(float(row[3]), 6),
        }
        for row in rows
    ]


def build_summary(
    config: DatabaseConfig,
    staging_rows: int,
    kpi_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    total_impressions = sum(row["impressions"] for row in kpi_rows)
    total_clicks = sum(row["clicks"] for row in kpi_rows)
    overall_ctr = 0.0 if total_impressions == 0 else total_clicks / total_impressions

    event_dates = [row["event_date"] for row in kpi_rows]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database_path": _display_path(config.database_path),
        "source_table": "stg_ad_events",
        "mart_table": MART_TABLE,
        "staging_row_count": staging_rows,
        "mart_row_count": len(kpi_rows),
        "total_impressions": total_impressions,
        "total_clicks": total_clicks,
        "overall_ctr": round(overall_ctr, 6),
        "date_range": {
            "min_event_date": min(event_dates) if event_dates else None,
            "max_event_date": max(event_dates) if event_dates else None,
        },
        "daily_kpis": kpi_rows,
        "success": len(kpi_rows) > 0 and total_impressions == staging_rows,
    }


def write_campaign_kpi_summary(summary: dict[str, Any], path: Path | None = None) -> Path:
    output_path = path or CAMPAIGN_KPI_SUMMARY
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2))
    return output_path


def run_campaign_kpis(
    config: DatabaseConfig | None = None,
    summary_path: Path | None = None,
) -> dict[str, Any]:
    config = config or load_config()
    ensure_database_ready(config)

    connection = duckdb.connect(str(config.database_path))
    try:
        staging_rows = ensure_staging_has_data(connection)
        clear_mart_table(connection)
        connection.execute(CAMPAIGN_KPI_INSERT_SQL)
        kpi_rows = fetch_campaign_kpis(connection)
    finally:
        connection.close()

    summary = build_summary(config, staging_rows, kpi_rows)
    write_campaign_kpi_summary(summary, summary_path)
    return summary


def main() -> int:
    print("=" * 60)
    print("Campaign KPI mart build")
    print("=" * 60)

    try:
        config = load_config()
        summary = run_campaign_kpis(config)

        print(f"Database: {config.database_path}")
        print(f"Source:   stg_ad_events ({summary['staging_row_count']:,} rows)")
        print(f"Mart:     {MART_TABLE} ({summary['mart_row_count']:,} daily rows)")
        print()
        for row in summary["daily_kpis"]:
            print(
                f"  {row['event_date']}: "
                f"{row['impressions']:,} impressions, "
                f"{row['clicks']:,} clicks, "
                f"CTR {row['ctr']:.4%}"
            )
        print()
        print(
            f"Overall CTR: {summary['overall_ctr']:.6f} "
            f"({summary['total_clicks']:,} / {summary['total_impressions']:,})"
        )
        print(f"Summary written to {CAMPAIGN_KPI_SUMMARY}")

        if not summary["success"]:
            print("Campaign KPI mart build did not reconcile with staging rows.", file=sys.stderr)
            return 1
        return 0

    except RuntimeError as exc:
        print(f"Campaign KPI build failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
