"""Ensure README/docs do not claim premature completion."""

from __future__ import annotations

import pytest

from helpers import DOCS_DIR, PROJECT_ROOT, README_WEEK2_COMPLETE_PHRASES, WEEK2_SCRIPTS_PENDING, read_text

pytestmark = [pytest.mark.docs, pytest.mark.unit]


README = read_text(PROJECT_ROOT / "README.md")


@pytest.mark.parametrize(
    "phrase",
    [
        "Tableau dashboard | ✅ Complete",
        "Excel stakeholder workbook | ✅ Complete",
        "Final README case study | ✅ Complete",
    ],
)
def test_readme_does_not_mark_future_phases_complete(phrase: str) -> None:
    assert phrase not in README


def test_readme_marks_week2_analytics_complete() -> None:
    for phrase in README_WEEK2_COMPLETE_PHRASES:
        assert phrase in README


def test_readme_marks_mart_exports_complete() -> None:
    assert "Mart exports for Tableau / Excel | ✅ Complete" in README


def test_readme_marks_recommendations_complete() -> None:
    assert "Recommendations + executive summary | ✅ Complete" in README


def test_readme_marks_ab_test_analysis_complete() -> None:
    assert "A/B test analysis | ✅ Complete" in README


def test_readme_marks_campaign_kpi_marts_complete() -> None:
    assert "Campaign KPI marts | ✅ Complete" in README
    assert "Funnel + segment analysis | ✅ Complete" in README
    assert "A/B test analysis | ✅ Complete" in README
    assert "CTR forecasting | ✅ Complete" in README


def test_readme_marks_s3_upload_complete() -> None:
    assert "AWS S3 setup + upload | ✅ Complete" in README


def test_readme_marks_duckdb_warehouse_setup_complete() -> None:
    assert "DuckDB warehouse setup | ✅ Complete" in README


def test_readme_marks_duckdb_load_validation_complete() -> None:
    assert "DuckDB load + validation | ✅ Complete" in README


def test_readme_marks_week1_lock_complete() -> None:
    assert "Week 1 tests + docs lock | ✅ Complete" in README


def test_schema_sql_files_exist_without_analytics_build_sql() -> None:
    sql_files = sorted((PROJECT_ROOT / "sql").glob("*.sql"))
    names = [path.name for path in sql_files]
    assert names == [
        "01_raw_tables.sql",
        "02_staging_tables.sql",
        "03_mart_tables.sql",
    ]


def test_upload_script_exists() -> None:
    assert (PROJECT_ROOT / "scripts" / "upload_to_s3.py").exists()


def test_duckdb_pipeline_scripts_exist_with_day13_exports() -> None:
    assert (PROJECT_ROOT / "scripts" / "create_duckdb_database.py").exists()
    assert (PROJECT_ROOT / "scripts" / "load_to_duckdb.py").exists()
    assert (PROJECT_ROOT / "scripts" / "validate_data.py").exists()
    assert (PROJECT_ROOT / "scripts" / "run_campaign_kpis.py").exists()
    assert (PROJECT_ROOT / "scripts" / "run_funnel_segment_analysis.py").exists()
    assert (PROJECT_ROOT / "scripts" / "run_ab_test_analysis.py").exists()
    assert (PROJECT_ROOT / "scripts" / "run_ctr_forecast.py").exists()
    assert (PROJECT_ROOT / "scripts" / "generate_recommendations.py").exists()
    assert (PROJECT_ROOT / "scripts" / "export_dashboard_data.py").exists()
    for script_name in WEEK2_SCRIPTS_PENDING:
        assert not (PROJECT_ROOT / "scripts" / script_name).exists()


def test_project_plan_mentions_day4_as_next_cloud_step() -> None:
    plan = read_text(DOCS_DIR / "project_plan.md")
    assert "Day 4" in plan or "| 4 |" in plan
    assert "S3" in plan
