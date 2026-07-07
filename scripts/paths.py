"""Shared project paths."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MARTS_DIR = DATA_DIR / "marts"
EXPORTS_DIR = DATA_DIR / "exports"
DOCS_DIR = PROJECT_ROOT / "docs"

AVAZU_RAW_CSV = RAW_DIR / "avazu_train.csv"
HILLSTROM_RAW_CSV = RAW_DIR / "hillstrom_email.csv"
RAW_PROFILE_SUMMARY = PROCESSED_DIR / "raw_profile_summary.json"

AVAZU_CLEAN_PARQUET = PROCESSED_DIR / "avazu_clean.parquet"
HILLSTROM_CLEAN_PARQUET = PROCESSED_DIR / "hillstrom_clean.parquet"
CLEANING_SUMMARY = PROCESSED_DIR / "cleaning_summary.json"
S3_UPLOAD_SUMMARY = PROCESSED_DIR / "s3_upload_summary.json"
DUCKDB_DEFAULT_PATH = PROCESSED_DIR / "marketing_analytics.duckdb"
DUCKDB_SETUP_SUMMARY = PROCESSED_DIR / "duckdb_setup_summary.json"
DUCKDB_LOAD_SUMMARY = PROCESSED_DIR / "duckdb_load_summary.json"
DATA_VALIDATION_SUMMARY = PROCESSED_DIR / "data_validation_summary.json"
WEEK1_DATA_LOCK_DOC = DOCS_DIR / "week1_data_lock.md"

SQL_DIR = PROJECT_ROOT / "sql"

AVAZU_COLUMNS = [
    "id",
    "click",
    "hour",
    "C1",
    "banner_pos",
    "site_id",
    "site_domain",
    "site_category",
    "app_id",
    "app_domain",
    "app_category",
    "device_id",
    "device_ip",
    "device_model",
    "device_type",
    "device_conn_type",
    "C14",
    "C15",
    "C16",
    "C17",
    "C18",
    "C19",
    "C20",
    "C21",
]
