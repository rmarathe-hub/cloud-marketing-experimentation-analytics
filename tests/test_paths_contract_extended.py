"""Extended paths.py contract tests."""

from __future__ import annotations

from pathlib import Path

import pytest

import paths
from helpers import PATH_CONSTANTS

pytestmark = [pytest.mark.unit, pytest.mark.week1]


@pytest.mark.parametrize("attr_name", PATH_CONSTANTS)
def test_paths_defines_constant(attr_name: str) -> None:
    value = getattr(paths, attr_name)
    assert isinstance(value, Path)


@pytest.mark.parametrize("attr_name", PATH_CONSTANTS)
def test_path_constant_inside_project_root(attr_name: str) -> None:
    root = paths.PROJECT_ROOT.resolve()
    value = getattr(paths, attr_name).resolve()
    assert str(value).startswith(str(root))


@pytest.mark.parametrize(
    "path_attr,expected_name",
    [
        ("AVAZU_RAW_CSV", "avazu_train.csv"),
        ("HILLSTROM_RAW_CSV", "hillstrom_email.csv"),
        ("AVAZU_CLEAN_PARQUET", "avazu_clean.parquet"),
        ("HILLSTROM_CLEAN_PARQUET", "hillstrom_clean.parquet"),
        ("RAW_PROFILE_SUMMARY", "raw_profile_summary.json"),
        ("CLEANING_SUMMARY", "cleaning_summary.json"),
        ("S3_UPLOAD_SUMMARY", "s3_upload_summary.json"),
        ("DUCKDB_DEFAULT_PATH", "marketing_analytics.duckdb"),
        ("DUCKDB_LOAD_SUMMARY", "duckdb_load_summary.json"),
        ("DATA_VALIDATION_SUMMARY", "data_validation_summary.json"),
        ("CAMPAIGN_KPI_SUMMARY", "campaign_kpi_summary.json"),
        ("FUNNEL_SEGMENT_SUMMARY", "funnel_segment_summary.json"),
        ("AB_TEST_SUMMARY", "ab_test_summary.json"),
        ("FORECAST_SUMMARY", "forecast_summary.json"),
        ("EXPORT_DASHBOARD_SUMMARY", "export_dashboard_summary.json"),
        ("EXCEL_WORKBOOK", "marketing_executive_workbook.xlsx"),
        ("MART_CAMPAIGN_KPIS_CSV", "campaign_kpis.csv"),
        ("MART_RECOMMENDATION_MATRIX_CSV", "recommendation_matrix.csv"),
        ("WEEK1_DATA_LOCK_DOC", "week1_data_lock.md"),
        ("WEEK2_ANALYTICS_LOCK_DOC", "week2_analytics_lock.md"),
    ],
)
def test_path_filenames(path_attr: str, expected_name: str) -> None:
    assert getattr(paths, path_attr).name == expected_name


def test_data_directories_under_data_dir() -> None:
    assert paths.RAW_DIR.parent == paths.DATA_DIR
    assert paths.PROCESSED_DIR.parent == paths.DATA_DIR
    assert paths.MARTS_DIR.parent == paths.DATA_DIR
    assert paths.EXPORTS_DIR.parent == paths.DATA_DIR


def test_sql_dir_contains_schema_files() -> None:
    names = {path.name for path in paths.SQL_DIR.glob("*.sql")}
    assert "01_raw_tables.sql" in names
    assert "03_mart_tables.sql" in names


def test_parent_directories_can_be_created(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(paths, "PROCESSED_DIR", tmp_path / "processed")
    paths.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    assert paths.PROCESSED_DIR.is_dir()
