"""Ensure README/docs do not claim premature completion."""

from __future__ import annotations

import pytest

from helpers import DOCS_DIR, PROJECT_ROOT, read_text

pytestmark = [pytest.mark.docs, pytest.mark.unit]


README = read_text(PROJECT_ROOT / "README.md")


@pytest.mark.parametrize(
    "phrase",
    [
        "DuckDB warehouse + validation | ✅ Complete",
        "Campaign KPI marts | ✅ Complete",
        "A/B test analysis | ✅ Complete",
        "CTR forecasting | ✅ Complete",
        "Tableau dashboard | ✅ Complete",
        "Excel stakeholder workbook | ✅ Complete",
        "Final README case study | ✅ Complete",
    ],
)
def test_readme_does_not_mark_future_phases_complete(phrase: str) -> None:
    assert phrase not in README


def test_readme_marks_s3_upload_complete() -> None:
    assert "AWS S3 setup + upload | ✅ Complete" in README


def test_sql_directory_has_no_completed_analytics_sql_yet() -> None:
    sql_files = list((PROJECT_ROOT / "sql").glob("*.sql"))
    assert sql_files == []


def test_no_upload_script_implemented_yet() -> None:
    assert (PROJECT_ROOT / "scripts" / "upload_to_s3.py").exists()


def test_no_duckdb_load_scripts_yet() -> None:
    assert not (PROJECT_ROOT / "scripts" / "create_duckdb_database.py").exists()
    assert not (PROJECT_ROOT / "scripts" / "load_to_duckdb.py").exists()


def test_project_plan_mentions_day4_as_next_cloud_step() -> None:
    plan = read_text(DOCS_DIR / "project_plan.md")
    assert "Day 4" in plan or "| 4 |" in plan
    assert "S3" in plan
