"""Shared helpers for the test suite."""

from __future__ import annotations

import importlib
import json
import subprocess
from pathlib import Path

import pandas as pd
import pytest

from paths import (
    AVAZU_COLUMNS,
    AVAZU_CLEAN_PARQUET,
    AVAZU_RAW_CSV,
    CLEANING_SUMMARY,
    HILLSTROM_CLEAN_PARQUET,
    HILLSTROM_RAW_CSV,
    PROJECT_ROOT,
    PROCESSED_DIR,
    RAW_PROFILE_SUMMARY,
)

SCRIPTS_DIR = PROJECT_ROOT / "scripts"
DOCS_DIR = PROJECT_ROOT / "docs"

REQUIRED_ROOT_FILES = [
    "README.md",
    "requirements.txt",
    ".gitignore",
    ".env.example",
]

REQUIRED_DIRS = [
    "data",
    "data/raw",
    "data/processed",
    "data/marts",
    "data/exports",
    "scripts",
    "sql",
    "tableau",
    "tableau/screenshots",
    "excel",
    "excel/screenshots",
    "docs",
    "tests",
]

REQUIRED_DOCS = [
    "business_problem.md",
    "metric_definitions.md",
    "data_dictionary.md",
    "project_plan.md",
    "cost_controls.md",
    "data_quality_report.md",
    "aws_s3_setup.md",
    "duckdb_setup.md",
    "week1_data_lock.md",
]

REQUIRED_SCRIPTS = [
    "paths.py",
    "download_or_import_data.py",
    "profile_raw_data.py",
    "cleaning_utils.py",
    "clean_avazu_ads.py",
    "clean_hillstrom_email.py",
    "upload_to_s3.py",
    "create_duckdb_database.py",
    "load_to_duckdb.py",
    "validate_data.py",
    "generate_week1_data_lock.py",
]

REQUIRED_PACKAGES = [
    "pandas",
    "numpy",
    "pyarrow",
    "scipy",
    "statsmodels",
    "duckdb",
    "boto3",
    "openpyxl",
    "pytest",
    "dotenv",
]

SQL_SCHEMA_FILES = [
    "01_raw_tables.sql",
    "02_staging_tables.sql",
    "03_mart_tables.sql",
]

WEEK2_ALL_SCRIPTS = [
    "run_campaign_kpis.py",
    "run_funnel_segment_analysis.py",
    "run_ab_test_analysis.py",
    "run_ctr_forecast.py",
    "export_dashboard_data.py",
]

WEEK2_SCRIPTS_IMPLEMENTED = (
    "run_campaign_kpis.py",
    "run_funnel_segment_analysis.py",
)

WEEK2_SCRIPTS_PENDING = tuple(
    script for script in WEEK2_ALL_SCRIPTS if script not in WEEK2_SCRIPTS_IMPLEMENTED
)

# Backward-compatible alias used by older tests.
WEEK2_SCRIPTS = WEEK2_SCRIPTS_PENDING

DUCKDB_RAW_TABLES = ("raw_avazu_ads", "raw_hillstrom_email")
DUCKDB_STAGING_TABLES = ("stg_ad_events", "stg_email_experiment")
DUCKDB_MART_TABLES = (
    "mart_campaign_kpis",
    "mart_ctr_trends",
    "mart_device_app_performance",
    "mart_ab_test_results",
    "mart_forecast_inputs",
    "mart_forecast_results",
)

DUCKDB_MART_TABLES_POPULATED = (
    "mart_campaign_kpis",
    "mart_ctr_trends",
    "mart_device_app_performance",
)

DUCKDB_MART_TABLES_PENDING = tuple(
    table for table in DUCKDB_MART_TABLES if table not in DUCKDB_MART_TABLES_POPULATED
)
DUCKDB_ALL_TABLES = DUCKDB_RAW_TABLES + DUCKDB_STAGING_TABLES + DUCKDB_MART_TABLES

S3_UPLOAD_LOCAL_FILES = (
    "data/raw/avazu_train.csv",
    "data/raw/hillstrom_email.csv",
    "data/processed/avazu_clean.parquet",
    "data/processed/hillstrom_clean.parquet",
)

S3_UPLOAD_KEYS = (
    "raw/avazu_train.csv",
    "raw/hillstrom_email.csv",
    "processed/avazu_clean.parquet",
    "processed/hillstrom_clean.parquet",
)

S3_FORBIDDEN_UPLOAD_PATTERNS = (
    ".env",
    "cleaning_summary.json",
    "data/marts/",
    "data/exports/",
)

WEEK1_LOCKED = {
    "avazu_rows": 500_000,
    "hillstrom_rows": 64_000,
    "avazu_clicks": 82_037,
    "avazu_ctr_pct": 16.4074,
    "avazu_ctr_ratio": 0.164074,
    "hillstrom_visit_rate_pct": 14.6781,
    "hillstrom_visit_rate_ratio": 0.146781,
    "hillstrom_conversion_rate_pct": 0.9031,
    "hillstrom_conversion_rate_ratio": 0.009031,
    "avazu_clean_columns": 36,
    "hillstrom_clean_columns": 19,
    "hillstrom_zip_typo_rows": 28_776,
    "control_recipients": 21_306,
    "mens_email_recipients": 21_307,
    "womens_email_recipients": 21_387,
    "duckdb_table_count": 10,
    "validation_check_count": 18,
    "s3_upload_count": 4,
    "avazu_device_id_unique": 41_413,
    "avazu_app_id_unique": 1_641,
    "avazu_site_id_unique": 1_704,
}

HILLSTROM_RAW_SEGMENTS = {
    "Womens E-Mail": 21_387,
    "Mens E-Mail": 21_307,
    "No E-Mail": 21_306,
}

HILLSTROM_CLEAN_GROUPS = {
    "womens_email": 21_387,
    "mens_email": 21_307,
    "control": 21_306,
}

AVAZU_RAW_COLUMNS = list(AVAZU_COLUMNS)

HILLSTROM_RAW_COLUMNS = [
    "recency",
    "history_segment",
    "history",
    "mens",
    "womens",
    "zip_code",
    "newbie",
    "channel",
    "segment",
    "visit",
    "conversion",
    "spend",
]

AVAZU_CLEAN_DERIVED_COLUMNS = [
    "event_date",
    "event_hour",
    "flag_missing_fields",
]

HILLSTROM_CLEAN_DERIVED_COLUMNS = [
    "treatment_group",
    "treatment_label",
    "converted",
    "revenue",
    "zip_code_std",
    "flag_zip_code_typo",
    "flag_missing_fields",
]

GITIGNORE_REQUIRED_FRAGMENTS = [
    ".env",
    ".venv/",
    "__pycache__/",
    "data/raw/*",
    "data/processed/*",
    "data/marts/*",
    "data/exports/*",
    "*.duckdb",
    ".DS_Store",
    "excel/*.xlsx",
    "*.twbx",
]

TRACKED_FORBIDDEN_PATTERNS = [
    r"^data/raw/.+\.(csv|parquet|json)$",
    r"^data/processed/.+\.(csv|parquet|json)$",
    r"^data/marts/.+\.csv$",
    r"^data/exports/.+\.csv$",
    r"^\.env$",
    r"^\.env\.save$",
    r"^\.venv/",
    r"__pycache__",
    r"\.DS_Store$",
    r"\.duckdb$",
    r"\.twbx$",
    r"excel/.+\.xlsx$",
    r"\.hyper$",
]

README_FORBIDDEN_COMPLETE_PHRASES = [
    "A/B test analysis | ✅ Complete",
    "CTR forecasting | ✅ Complete",
    "Tableau dashboard | ✅ Complete",
    "Excel stakeholder workbook | ✅ Complete",
    "Final README case study | ✅ Complete",
]

README_WEEK1_COMPLETE_PHRASES = [
    "Repo scaffold + business framing | ✅ Complete",
    "Dataset acquisition + profiling | ✅ Complete",
    "Cleaning pipeline | ✅ Complete",
    "AWS S3 setup + upload | ✅ Complete",
    "DuckDB warehouse setup | ✅ Complete",
    "DuckDB load + validation | ✅ Complete",
    "Week 1 tests + docs lock | ✅ Complete",
]

PATH_CONSTANTS = [
    "PROJECT_ROOT",
    "DATA_DIR",
    "RAW_DIR",
    "PROCESSED_DIR",
    "MARTS_DIR",
    "EXPORTS_DIR",
    "DOCS_DIR",
    "AVAZU_RAW_CSV",
    "HILLSTROM_RAW_CSV",
    "RAW_PROFILE_SUMMARY",
    "AVAZU_CLEAN_PARQUET",
    "HILLSTROM_CLEAN_PARQUET",
    "CLEANING_SUMMARY",
    "S3_UPLOAD_SUMMARY",
    "DUCKDB_DEFAULT_PATH",
    "DUCKDB_SETUP_SUMMARY",
    "DUCKDB_LOAD_SUMMARY",
    "DATA_VALIDATION_SUMMARY",
    "CAMPAIGN_KPI_SUMMARY",
    "FUNNEL_SEGMENT_SUMMARY",
    "WEEK1_DATA_LOCK_DOC",
    "SQL_DIR",
]

SCRIPTS_WITH_MAIN = [
    name for name in REQUIRED_SCRIPTS if name not in {"paths.py", "cleaning_utils.py"}
] + list(WEEK2_SCRIPTS_IMPLEMENTED)

SCRIPTS_HELPER_ONLY = ["paths.py", "cleaning_utils.py"]

SECRET_PATTERNS = [
    "AKIA",
    "aws_secret_access_key",
    "BEGIN RSA PRIVATE KEY",
    "BEGIN OPENSSH PRIVATE KEY",
    "ghp_",
    "github_pat_",
    "kaggle.json",
]

# Files that intentionally reference secret pattern names for detection tests.
SECRET_PATTERN_SCAN_EXEMPT = {
    "tests/helpers.py",
    "tests/test_git_hygiene.py",
    "tests/test_script_imports.py",
    "tests/test_upload_to_s3.py",
    "tests/test_security_hygiene_extended.py",
    "tests/test_s3_contract_extended.py",
    "tests/test_week1_lock_contract.py",
}

PLACEHOLDER_ENV_VALUES = {
    "your-bucket-name",
    "your_kaggle_username",
    "your_kaggle_api_key",
}


def project_path(*parts: str) -> Path:
    return PROJECT_ROOT.joinpath(*parts)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def git_tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def skip_if_missing(path: Path, reason: str | None = None):
    if not path.exists():
        pytest.skip(reason or f"Missing required file: {path}")


def assert_approx_percent(actual: float, expected: float, tolerance: float = 0.05) -> None:
    assert abs(actual - expected) <= tolerance, f"{actual} not within {tolerance} of {expected}"


def assert_approx_ratio(actual: float, expected: float, tolerance: float = 0.001) -> None:
    assert abs(actual - expected) <= tolerance, f"{actual} not within {tolerance} of {expected}"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def import_module_clean(module_name: str):
    return importlib.import_module(module_name)


def tiny_avazu_rows() -> list[dict]:
    return [
        {
            "id": "1001",
            "click": 1,
            "hour": 14102108,
            "C1": 1005,
            "banner_pos": 0,
            "site_id": "site_a",
            "site_domain": "dom_a",
            "site_category": "cat_a",
            "app_id": "app_a",
            "app_domain": "appdom_a",
            "app_category": "appcat_a",
            "device_id": "dev_a",
            "device_ip": "ip_a",
            "device_model": "model_a",
            "device_type": 1,
            "device_conn_type": 2,
            "C14": 100,
            "C15": 320,
            "C16": 50,
            "C17": 1000,
            "C18": 0,
            "C19": 35,
            "C20": 100,
            "C21": 79,
        },
        {
            "id": "1002",
            "click": 0,
            "hour": 14102109,
            "C1": 1005,
            "banner_pos": 1,
            "site_id": "",
            "site_domain": "dom_b",
            "site_category": "cat_b",
            "app_id": "app_b",
            "app_domain": "appdom_b",
            "app_category": "appcat_b",
            "device_id": "dev_b",
            "device_ip": "ip_b",
            "device_model": "model_b",
            "device_type": -1,
            "device_conn_type": 2,
            "C14": 200,
            "C15": 320,
            "C16": 50,
            "C17": 1001,
            "C18": 0,
            "C19": 35,
            "C20": 101,
            "C21": 80,
        },
        {
            "id": "1003",
            "click": 9,
            "hour": 99999999,
            "C1": 1005,
            "banner_pos": 2,
            "site_id": "site_c",
            "site_domain": "dom_c",
            "site_category": "cat_c",
            "app_id": "app_c",
            "app_domain": "appdom_c",
            "app_category": "appcat_c",
            "device_id": "dev_c",
            "device_ip": "ip_c",
            "device_model": "model_c",
            "device_type": 0,
            "device_conn_type": 2,
            "C14": 300,
            "C15": 320,
            "C16": 50,
            "C17": 1002,
            "C18": 0,
            "C19": 35,
            "C20": 102,
            "C21": 81,
        },
    ]


def tiny_avazu_dataframe() -> pd.DataFrame:
    return pd.DataFrame(tiny_avazu_rows())


def tiny_hillstrom_rows() -> list[dict]:
    return [
        {
            "recency": 10,
            "history_segment": "2) $100 - $200",
            "history": 142.44,
            "mens": 1,
            "womens": 0,
            "zip_code": "Surburban",
            "newbie": 0,
            "channel": "Phone",
            "segment": "Womens E-Mail",
            "visit": 1,
            "conversion": 0,
            "spend": 25.0,
        },
        {
            "recency": 6,
            "history_segment": "3) $200 - $350",
            "history": 329.08,
            "mens": 1,
            "womens": 1,
            "zip_code": "Rural",
            "newbie": 1,
            "channel": "Web",
            "segment": "No E-Mail",
            "visit": 0,
            "conversion": 0,
            "spend": 0.0,
        },
        {
            "recency": 7,
            "history_segment": "2) $100 - $200",
            "history": 180.65,
            "mens": 0,
            "womens": 1,
            "zip_code": "Urban",
            "newbie": 0,
            "channel": "Web",
            "segment": "Mens E-Mail",
            "visit": 1,
            "conversion": 1,
            "spend": 50.0,
        },
        {
            "recency": 3,
            "history_segment": "1) $0 - $100",
            "history": 45.34,
            "mens": 0,
            "womens": 0,
            "zip_code": "Urban",
            "newbie": 1,
            "channel": "Phone",
            "segment": "Mens E-Mail",
            "visit": 0,
            "conversion": 0,
            "spend": 10.0,
        },
    ]


def tiny_hillstrom_dataframe() -> pd.DataFrame:
    return pd.DataFrame(tiny_hillstrom_rows())


def write_tiny_avazu_csv(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(tiny_avazu_rows()).to_csv(path, index=False)
    return path


def write_tiny_hillstrom_csv(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(tiny_hillstrom_rows()).to_csv(path, index=False)
    return path


def local_data_available() -> bool:
    return AVAZU_RAW_CSV.exists() and HILLSTROM_RAW_CSV.exists()


def local_processed_available() -> bool:
    return (
        RAW_PROFILE_SUMMARY.exists()
        and CLEANING_SUMMARY.exists()
        and AVAZU_CLEAN_PARQUET.exists()
        and HILLSTROM_CLEAN_PARQUET.exists()
    )


def local_duckdb_available() -> bool:
    from paths import DUCKDB_DEFAULT_PATH

    return DUCKDB_DEFAULT_PATH.exists()


def production_load_summary_available() -> bool:
    from paths import DUCKDB_LOAD_SUMMARY

    if not DUCKDB_LOAD_SUMMARY.exists():
        return False
    payload = load_json(DUCKDB_LOAD_SUMMARY)
    loads = {item["table_name"]: item for item in payload.get("loads", [])}
    return loads.get("raw_avazu_ads", {}).get("row_count", 0) >= 100_000


def production_validation_summary_available() -> bool:
    from paths import DATA_VALIDATION_SUMMARY

    if not DATA_VALIDATION_SUMMARY.exists():
        return False
    payload = load_json(DATA_VALIDATION_SUMMARY)
    return payload.get("success") is True and payload.get("passed_count", 0) >= WEEK1_LOCKED["validation_check_count"]


def run_implemented_week2_analytics(config, processed_dir: Path) -> None:
    """Run all implemented Week 2 analytics scripts (for validation integration tests)."""
    import run_campaign_kpis as campaign_kpis
    import run_funnel_segment_analysis as funnel_segment

    campaign_kpis.run_campaign_kpis(
        config=config,
        summary_path=processed_dir / "campaign_kpi_summary.json",
    )
    funnel_segment.run_funnel_segment_analysis(
        config=config,
        summary_path=processed_dir / "funnel_segment_summary.json",
    )


def assert_no_secret_patterns(text: str, source: str = "content") -> None:
    lowered = text.lower()
    for pattern in SECRET_PATTERNS:
        assert pattern.lower() not in lowered, f"{source} contains forbidden pattern {pattern}"


def import_script_fresh(module_name: str):
    import sys

    full_name = module_name.replace(".py", "")
    if full_name in sys.modules:
        del sys.modules[full_name]
    return importlib.import_module(full_name)
