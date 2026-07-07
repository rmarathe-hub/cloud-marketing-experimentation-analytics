#!/usr/bin/env python3
"""Create the local DuckDB warehouse schema (empty tables, no data load)."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb
from dotenv import load_dotenv

from paths import (
    DUCKDB_DEFAULT_PATH,
    DUCKDB_SETUP_SUMMARY,
    PROJECT_ROOT,
    SQL_DIR,
)

SCHEMA_FILES = (
    "01_raw_tables.sql",
    "02_staging_tables.sql",
    "03_mart_tables.sql",
)

EXPECTED_TABLES: dict[str, str] = {
    "raw_avazu_ads": "raw",
    "raw_hillstrom_email": "raw",
    "stg_ad_events": "staging",
    "stg_email_experiment": "staging",
    "mart_campaign_kpis": "mart",
    "mart_ctr_trends": "mart",
    "mart_device_app_performance": "mart",
    "mart_ab_test_results": "mart",
    "mart_forecast_inputs": "mart",
    "mart_forecast_results": "mart",
}


@dataclass(frozen=True)
class DatabaseConfig:
    database_path: Path


def load_config(env_path: Path | None = None) -> DatabaseConfig:
    load_dotenv(env_path or PROJECT_ROOT / ".env")

    configured = os.getenv("DUCKDB_PATH", "").strip()
    if configured:
        database_path = Path(configured)
        if not database_path.is_absolute():
            database_path = PROJECT_ROOT / database_path
    else:
        database_path = DUCKDB_DEFAULT_PATH

    return DatabaseConfig(database_path=database_path)


def get_schema_files(sql_dir: Path | None = None) -> list[Path]:
    base = sql_dir or SQL_DIR
    files = [base / name for name in SCHEMA_FILES]
    missing = [str(path) for path in files if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Missing required SQL schema files:\n  - " + "\n  - ".join(missing)
        )
    return files


def execute_schema_sql(connection: duckdb.DuckDBPyConnection, sql_files: list[Path]) -> None:
    for sql_file in sql_files:
        connection.execute(sql_file.read_text(encoding="utf-8"))


def list_table_metadata(connection: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    metadata: list[dict[str, Any]] = []

    for table_name, layer in EXPECTED_TABLES.items():
        exists = connection.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'main' AND table_name = ?
            """,
            [table_name],
        ).fetchone()[0]

        if not exists:
            raise RuntimeError(f"Expected table was not created: {table_name}")

        row_count = connection.execute(
            f"SELECT COUNT(*) FROM {table_name}"
        ).fetchone()[0]

        metadata.append(
            {
                "table_name": table_name,
                "layer": layer,
                "row_count": int(row_count),
            }
        )

    return metadata


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def build_summary(
    config: DatabaseConfig,
    tables: list[dict[str, Any]],
    sql_files: list[Path],
) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database_path": _display_path(config.database_path),
        "schema_files": [path.name for path in sql_files],
        "tables": tables,
        "table_count": len(tables),
        "data_loaded": False,
        "success": True,
    }


def write_setup_summary(summary: dict[str, Any], path: Path | None = None) -> Path:
    output_path = path or DUCKDB_SETUP_SUMMARY
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2))
    return output_path


def create_database(
    config: DatabaseConfig | None = None,
    sql_dir: Path | None = None,
    summary_path: Path | None = None,
) -> dict[str, Any]:
    config = config or load_config()
    sql_files = get_schema_files(sql_dir)

    config.database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = duckdb.connect(str(config.database_path))
    try:
        execute_schema_sql(connection, sql_files)
        tables = list_table_metadata(connection)
    finally:
        connection.close()

    summary = build_summary(config, tables, sql_files)
    write_setup_summary(summary, summary_path)
    return summary


def main() -> int:
    print("=" * 60)
    print("DuckDB warehouse setup")
    print("=" * 60)

    try:
        config = load_config()
        summary = create_database(config)

        print(f"Database: {config.database_path}")
        print(f"Tables:   {summary['table_count']} empty tables created")
        print()
        for table in summary["tables"]:
            print(
                f"  - {table['table_name']} ({table['layer']}) "
                f"[{table['row_count']} rows]"
            )

        print()
        print(f"Summary written to {DUCKDB_SETUP_SUMMARY}")
        print("Data load not performed (Day 6).")
        return 0

    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        print(f"Database setup failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
