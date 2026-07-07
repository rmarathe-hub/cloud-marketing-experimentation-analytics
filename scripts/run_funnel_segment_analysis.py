#!/usr/bin/env python3
"""Build funnel and segmentation marts from stg_ad_events."""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import duckdb

from create_duckdb_database import DatabaseConfig, _display_path, load_config
from paths import FUNNEL_SEGMENT_SUMMARY

CTR_TRENDS_TABLE = "mart_ctr_trends"
DEVICE_APP_TABLE = "mart_device_app_performance"
DEFAULT_MIN_IMPRESSIONS_FOR_RANKING = 1_000

CTR_TRENDS_INSERT_SQL = """
INSERT INTO mart_ctr_trends (event_date, event_hour, impressions, clicks, ctr)
SELECT
    event_date,
    event_hour,
    COUNT(*)::BIGINT AS impressions,
    SUM(click)::BIGINT AS clicks,
    CASE
        WHEN COUNT(*) = 0 THEN 0.0
        ELSE SUM(click)::DOUBLE / COUNT(*)::DOUBLE
    END AS ctr
FROM stg_ad_events
WHERE event_date IS NOT NULL AND event_hour IS NOT NULL
GROUP BY event_date, event_hour
ORDER BY event_date, event_hour
"""

DEVICE_APP_INSERT_SQL = """
INSERT INTO mart_device_app_performance (
    device_type,
    app_category,
    site_category,
    banner_pos,
    impressions,
    clicks,
    ctr,
    click_share
)
WITH segment_metrics AS (
    SELECT
        device_type,
        app_category,
        site_category,
        banner_pos,
        COUNT(*)::BIGINT AS impressions,
        SUM(click)::BIGINT AS clicks,
        CASE
            WHEN COUNT(*) = 0 THEN 0.0
            ELSE SUM(click)::DOUBLE / COUNT(*)::DOUBLE
        END AS ctr
    FROM stg_ad_events
    GROUP BY device_type, app_category, site_category, banner_pos
),
total_clicks AS (
    SELECT COALESCE(SUM(clicks), 0)::DOUBLE AS total_clicks
    FROM segment_metrics
)
SELECT
    segment_metrics.device_type,
    segment_metrics.app_category,
    segment_metrics.site_category,
    segment_metrics.banner_pos,
    segment_metrics.impressions,
    segment_metrics.clicks,
    segment_metrics.ctr,
    CASE
        WHEN total_clicks.total_clicks = 0 THEN 0.0
        ELSE segment_metrics.clicks::DOUBLE / total_clicks.total_clicks
    END AS click_share
FROM segment_metrics
CROSS JOIN total_clicks
ORDER BY segment_metrics.ctr DESC, segment_metrics.impressions DESC
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


def clear_mart_tables(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute(f"DELETE FROM {CTR_TRENDS_TABLE}")
    connection.execute(f"DELETE FROM {DEVICE_APP_TABLE}")


def fetch_hourly_trends(connection: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    rows = connection.execute(
        f"""
        SELECT event_date, event_hour, impressions, clicks, ctr
        FROM {CTR_TRENDS_TABLE}
        ORDER BY event_date, event_hour
        """
    ).fetchall()
    return [
        {
            "event_date": row[0].isoformat() if isinstance(row[0], date) else str(row[0]),
            "event_hour": int(row[1]),
            "impressions": int(row[2]),
            "clicks": int(row[3]),
            "ctr": round(float(row[4]), 6),
        }
        for row in rows
    ]


def fetch_segment_rankings(
    connection: duckdb.DuckDBPyConnection,
    min_impressions: int,
    limit: int = 5,
) -> dict[str, list[dict[str, Any]]]:
    rows = connection.execute(
        f"""
        SELECT
            device_type,
            app_category,
            site_category,
            banner_pos,
            impressions,
            clicks,
            ctr,
            click_share
        FROM {DEVICE_APP_TABLE}
        WHERE impressions >= ?
        ORDER BY ctr DESC, impressions DESC
        LIMIT ?
        """,
        [min_impressions, limit],
    ).fetchall()
    top_segments = [
        {
            "device_type": int(row[0]) if row[0] is not None else None,
            "app_category": row[1],
            "site_category": row[2],
            "banner_pos": int(row[3]) if row[3] is not None else None,
            "impressions": int(row[4]),
            "clicks": int(row[5]),
            "ctr": round(float(row[6]), 6),
            "click_share": round(float(row[7]), 6),
        }
        for row in rows
    ]

    bottom_rows = connection.execute(
        f"""
        SELECT
            device_type,
            app_category,
            site_category,
            banner_pos,
            impressions,
            clicks,
            ctr,
            click_share
        FROM {DEVICE_APP_TABLE}
        WHERE impressions >= ?
        ORDER BY ctr ASC, impressions DESC
        LIMIT ?
        """,
        [min_impressions, limit],
    ).fetchall()
    bottom_segments = [
        {
            "device_type": int(row[0]) if row[0] is not None else None,
            "app_category": row[1],
            "site_category": row[2],
            "banner_pos": int(row[3]) if row[3] is not None else None,
            "impressions": int(row[4]),
            "clicks": int(row[5]),
            "ctr": round(float(row[6]), 6),
            "click_share": round(float(row[7]), 6),
        }
        for row in bottom_rows
    ]
    return {"top_by_ctr": top_segments, "bottom_by_ctr": bottom_segments}


def build_summary(
    config: DatabaseConfig,
    staging_rows: int,
    hourly_rows: list[dict[str, Any]],
    segment_rankings: dict[str, list[dict[str, Any]]],
    ctr_trends_count: int,
    device_app_count: int,
    min_impressions: int,
) -> dict[str, Any]:
    hourly_impressions = sum(row["impressions"] for row in hourly_rows)
    hourly_clicks = sum(row["clicks"] for row in hourly_rows)
    hourly_ctr = 0.0 if hourly_impressions == 0 else hourly_clicks / hourly_impressions

    ctr_values = [row["ctr"] for row in hourly_rows]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database_path": _display_path(config.database_path),
        "source_table": "stg_ad_events",
        "staging_row_count": staging_rows,
        "min_impressions_for_ranking": min_impressions,
        "marts": {
            CTR_TRENDS_TABLE: {
                "row_count": ctr_trends_count,
                "total_impressions": hourly_impressions,
                "total_clicks": hourly_clicks,
                "overall_ctr": round(hourly_ctr, 6),
                "hourly_ctr_range": {
                    "min_ctr": round(min(ctr_values), 6) if ctr_values else None,
                    "max_ctr": round(max(ctr_values), 6) if ctr_values else None,
                },
            },
            DEVICE_APP_TABLE: {
                "row_count": device_app_count,
            },
        },
        "segment_rankings": segment_rankings,
        "success": (
            ctr_trends_count > 0
            and device_app_count > 0
            and hourly_impressions == staging_rows
        ),
    }


def write_funnel_segment_summary(summary: dict[str, Any], path: Path | None = None) -> Path:
    output_path = path or FUNNEL_SEGMENT_SUMMARY
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2))
    return output_path


def run_funnel_segment_analysis(
    config: DatabaseConfig | None = None,
    summary_path: Path | None = None,
    min_impressions_for_ranking: int = DEFAULT_MIN_IMPRESSIONS_FOR_RANKING,
) -> dict[str, Any]:
    config = config or load_config()
    ensure_database_ready(config)

    connection = duckdb.connect(str(config.database_path))
    try:
        staging_rows = ensure_staging_has_data(connection)
        clear_mart_tables(connection)
        connection.execute(CTR_TRENDS_INSERT_SQL)
        connection.execute(DEVICE_APP_INSERT_SQL)

        ctr_trends_count = int(
            connection.execute(f"SELECT COUNT(*) FROM {CTR_TRENDS_TABLE}").fetchone()[0]
        )
        device_app_count = int(
            connection.execute(f"SELECT COUNT(*) FROM {DEVICE_APP_TABLE}").fetchone()[0]
        )
        hourly_rows = fetch_hourly_trends(connection)
        segment_rankings = fetch_segment_rankings(
            connection,
            min_impressions=min_impressions_for_ranking,
        )
    finally:
        connection.close()

    summary = build_summary(
        config=config,
        staging_rows=staging_rows,
        hourly_rows=hourly_rows,
        segment_rankings=segment_rankings,
        ctr_trends_count=ctr_trends_count,
        device_app_count=device_app_count,
        min_impressions=min_impressions_for_ranking,
    )
    write_funnel_segment_summary(summary, summary_path)
    return summary


def main() -> int:
    print("=" * 60)
    print("Funnel + segmentation mart build")
    print("=" * 60)

    try:
        config = load_config()
        summary = run_funnel_segment_analysis(config)

        ctr_summary = summary["marts"][CTR_TRENDS_TABLE]
        device_summary = summary["marts"][DEVICE_APP_TABLE]

        print(f"Database: {config.database_path}")
        print(f"Source:   stg_ad_events ({summary['staging_row_count']:,} rows)")
        print()
        print(
            f"{CTR_TRENDS_TABLE}: {ctr_summary['row_count']:,} hourly rows, "
            f"CTR {ctr_summary['overall_ctr']:.4%}"
        )
        print(f"{DEVICE_APP_TABLE}: {device_summary['row_count']:,} segment rows")
        print()
        print("Top segments by CTR:")
        for row in summary["segment_rankings"]["top_by_ctr"][:3]:
            print(
                f"  device={row['device_type']} app={row['app_category']} "
                f"site={row['site_category']} banner={row['banner_pos']}: "
                f"CTR {row['ctr']:.4%} ({row['impressions']:,} impressions)"
            )
        print()
        print(f"Summary written to {FUNNEL_SEGMENT_SUMMARY}")

        if not summary["success"]:
            print("Funnel/segment mart build did not reconcile with staging rows.", file=sys.stderr)
            return 1
        return 0

    except RuntimeError as exc:
        print(f"Funnel/segment build failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
