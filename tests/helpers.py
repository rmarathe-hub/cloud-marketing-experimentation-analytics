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
]

REQUIRED_SCRIPTS = [
    "paths.py",
    "download_or_import_data.py",
    "profile_raw_data.py",
    "cleaning_utils.py",
    "clean_avazu_ads.py",
    "clean_hillstrom_email.py",
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
]

SECRET_PATTERNS = [
    "AKIA",
    "aws_secret_access_key",
    "BEGIN RSA PRIVATE KEY",
    "BEGIN OPENSSH PRIVATE KEY",
    "ghp_",
    "github_pat_",
    "kaggle.json",
]

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
        and (PROCESSED_DIR / "avazu_clean.parquet").exists()
        and (PROCESSED_DIR / "hillstrom_clean.parquet").exists()
    )
