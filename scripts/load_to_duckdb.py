#!/usr/bin/env python3
"""Load local raw CSV and cleaned Parquet files into DuckDB."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb

from create_duckdb_database import DatabaseConfig, _display_path, load_config
from paths import (
    AVAZU_CLEAN_PARQUET,
    AVAZU_RAW_CSV,
    DUCKDB_LOAD_SUMMARY,
    HILLSTROM_CLEAN_PARQUET,
    HILLSTROM_RAW_CSV,
)

LOAD_TABLES = (
    "raw_avazu_ads",
    "raw_hillstrom_email",
    "stg_ad_events",
    "stg_email_experiment",
)

AVAZU_RAW_INSERT_SQL = """
INSERT INTO raw_avazu_ads
SELECT
    CAST(id AS VARCHAR) AS id,
    CAST(click AS INTEGER) AS click,
    CAST(hour AS BIGINT) AS hour,
    CAST("C1" AS BIGINT) AS c1,
    CAST(banner_pos AS INTEGER) AS banner_pos,
    CAST(site_id AS VARCHAR) AS site_id,
    CAST(site_domain AS VARCHAR) AS site_domain,
    CAST(site_category AS VARCHAR) AS site_category,
    CAST(app_id AS VARCHAR) AS app_id,
    CAST(app_domain AS VARCHAR) AS app_domain,
    CAST(app_category AS VARCHAR) AS app_category,
    CAST(device_id AS VARCHAR) AS device_id,
    CAST(device_ip AS VARCHAR) AS device_ip,
    CAST(device_model AS VARCHAR) AS device_model,
    CAST(device_type AS INTEGER) AS device_type,
    CAST(device_conn_type AS INTEGER) AS device_conn_type,
    CAST("C14" AS DOUBLE) AS c14,
    CAST("C15" AS DOUBLE) AS c15,
    CAST("C16" AS DOUBLE) AS c16,
    CAST("C17" AS DOUBLE) AS c17,
    CAST("C18" AS DOUBLE) AS c18,
    CAST("C19" AS DOUBLE) AS c19,
    CAST("C20" AS DOUBLE) AS c20,
    CAST("C21" AS DOUBLE) AS c21
FROM read_csv(?, header=true)
"""

HILLSTROM_RAW_INSERT_SQL = """
INSERT INTO raw_hillstrom_email
SELECT
    CAST(recency AS INTEGER) AS recency,
    CAST(history_segment AS VARCHAR) AS history_segment,
    CAST(history AS DOUBLE) AS history,
    CAST(mens AS INTEGER) AS mens,
    CAST(womens AS INTEGER) AS womens,
    CAST(zip_code AS VARCHAR) AS zip_code,
    CAST(newbie AS INTEGER) AS newbie,
    CAST(channel AS VARCHAR) AS channel,
    CAST(segment AS VARCHAR) AS segment,
    CAST(visit AS INTEGER) AS visit,
    CAST(conversion AS INTEGER) AS conversion,
    CAST(spend AS DOUBLE) AS spend
FROM read_csv(?, header=true)
"""


@dataclass(frozen=True)
class LoadTarget:
    table_name: str
    layer: str
    source_path: Path
    source_type: str


def get_load_targets(
    avazu_raw: Path | None = None,
    hillstrom_raw: Path | None = None,
    avazu_clean: Path | None = None,
    hillstrom_clean: Path | None = None,
) -> list[LoadTarget]:
    return [
        LoadTarget("raw_avazu_ads", "raw", avazu_raw or AVAZU_RAW_CSV, "csv"),
        LoadTarget(
            "raw_hillstrom_email",
            "raw",
            hillstrom_raw or HILLSTROM_RAW_CSV,
            "csv",
        ),
        LoadTarget("stg_ad_events", "staging", avazu_clean or AVAZU_CLEAN_PARQUET, "parquet"),
        LoadTarget(
            "stg_email_experiment",
            "staging",
            hillstrom_clean or HILLSTROM_CLEAN_PARQUET,
            "parquet",
        ),
    ]


def validate_local_sources(targets: list[LoadTarget]) -> None:
    missing = [str(target.source_path) for target in targets if not target.source_path.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing required local files before DuckDB load:\n  - " + "\n  - ".join(missing)
        )


def ensure_database_ready(config: DatabaseConfig) -> None:
    if not config.database_path.exists():
        raise RuntimeError(
            f"DuckDB database not found at {config.database_path}. "
            "Run `python scripts/create_duckdb_database.py` first."
        )


def clear_load_tables(connection: duckdb.DuckDBPyConnection) -> None:
    for table_name in LOAD_TABLES:
        connection.execute(f"DELETE FROM {table_name}")


def load_table(connection: duckdb.DuckDBPyConnection, target: LoadTarget) -> int:
    if target.table_name == "raw_avazu_ads":
        connection.execute(AVAZU_RAW_INSERT_SQL, [str(target.source_path)])
    elif target.table_name == "raw_hillstrom_email":
        connection.execute(HILLSTROM_RAW_INSERT_SQL, [str(target.source_path)])
    else:
        connection.execute(
            f"INSERT INTO {target.table_name} SELECT * FROM read_parquet(?)",
            [str(target.source_path)],
        )

    row_count = connection.execute(
        f"SELECT COUNT(*) FROM {target.table_name}"
    ).fetchone()[0]
    return int(row_count)


def build_load_summary(
    config: DatabaseConfig,
    loads: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database_path": _display_path(config.database_path),
        "loads": loads,
        "loaded_table_count": len(loads),
        "success": all(item["status"] == "success" for item in loads),
    }


def write_load_summary(summary: dict[str, Any], path: Path | None = None) -> Path:
    output_path = path or DUCKDB_LOAD_SUMMARY
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2))
    return output_path


def load_data(
    config: DatabaseConfig | None = None,
    targets: list[LoadTarget] | None = None,
    summary_path: Path | None = None,
) -> dict[str, Any]:
    config = config or load_config()
    targets = targets or get_load_targets()

    validate_local_sources(targets)
    ensure_database_ready(config)

    loads: list[dict[str, Any]] = []
    connection = duckdb.connect(str(config.database_path))
    try:
        clear_load_tables(connection)
        for target in targets:
            entry = {
                "table_name": target.table_name,
                "layer": target.layer,
                "source_file": _display_path(target.source_path),
                "source_type": target.source_type,
                "row_count": 0,
                "status": "pending",
                "error": None,
            }
            try:
                row_count = load_table(connection, target)
                entry["row_count"] = row_count
                entry["status"] = "success"
            except duckdb.Error as exc:
                entry["status"] = "failed"
                entry["error"] = exc.__class__.__name__
                loads.append(entry)
                break
            loads.append(entry)
    finally:
        connection.close()

    summary = build_load_summary(config, loads)
    write_load_summary(summary, summary_path)
    return summary


def main() -> int:
    print("=" * 60)
    print("DuckDB data load")
    print("=" * 60)

    try:
        config = load_config()
        summary = load_data(config)

        print(f"Database: {config.database_path}")
        print()
        for item in summary["loads"]:
            status = "✓" if item["status"] == "success" else "✗"
            print(
                f"{status} {item['source_file']} -> {item['table_name']} "
                f"({item['row_count']:,} rows)"
            )

        print()
        print(f"Summary written to {DUCKDB_LOAD_SUMMARY}")

        if not summary["success"]:
            print("One or more tables failed to load.", file=sys.stderr)
            return 1
        return 0

    except (FileNotFoundError, RuntimeError) as exc:
        print(f"Load failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
