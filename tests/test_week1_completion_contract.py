"""Week 1 Days 1-7 completion contract tests."""

from __future__ import annotations

import pytest

from helpers import (
    DOCS_DIR,
    PROJECT_ROOT,
    README_FORBIDDEN_COMPLETE_PHRASES,
    README_WEEK1_COMPLETE_PHRASES,
    REQUIRED_DIRS,
    REQUIRED_DOCS,
    REQUIRED_ROOT_FILES,
    REQUIRED_SCRIPTS,
    SQL_SCHEMA_FILES,
    WEEK2_SCRIPTS,
    read_text,
)

pytestmark = [pytest.mark.week1, pytest.mark.unit]


@pytest.mark.parametrize("filename", REQUIRED_ROOT_FILES)
def test_required_root_file_exists(filename: str) -> None:
    assert (PROJECT_ROOT / filename).is_file()


@pytest.mark.parametrize("dirname", REQUIRED_DIRS)
def test_required_directory_exists(dirname: str) -> None:
    assert (PROJECT_ROOT / dirname).is_dir()


@pytest.mark.parametrize("doc_name", REQUIRED_DOCS)
def test_required_doc_exists(doc_name: str) -> None:
    assert (DOCS_DIR / doc_name).is_file()


@pytest.mark.parametrize("script_name", REQUIRED_SCRIPTS)
def test_required_script_exists(script_name: str) -> None:
    assert (PROJECT_ROOT / "scripts" / script_name).is_file()


@pytest.mark.parametrize("sql_file", SQL_SCHEMA_FILES)
def test_required_sql_schema_exists(sql_file: str) -> None:
    assert (PROJECT_ROOT / "sql" / sql_file).is_file()


@pytest.mark.parametrize("script_name", WEEK2_SCRIPTS)
def test_week2_script_does_not_exist(script_name: str) -> None:
    assert not (PROJECT_ROOT / "scripts" / script_name).exists()


@pytest.mark.parametrize("phrase", README_WEEK1_COMPLETE_PHRASES)
def test_readme_marks_week1_phases_complete(phrase: str) -> None:
    assert phrase in read_text(PROJECT_ROOT / "README.md")


@pytest.mark.parametrize("phrase", README_FORBIDDEN_COMPLETE_PHRASES)
def test_readme_does_not_mark_week2_complete(phrase: str) -> None:
    assert phrase not in read_text(PROJECT_ROOT / "README.md")


@pytest.mark.parametrize(
    "forbidden_phrase",
    [
        "Week 2 analytics | ✅ Complete",
        "mart tables populated",
        "Tableau dashboard complete",
        "Excel workbook complete",
    ],
)
def test_readme_does_not_claim_future_deliverables(forbidden_phrase: str) -> None:
    readme = read_text(PROJECT_ROOT / "README.md").lower()
    assert forbidden_phrase.lower() not in readme


def test_no_tableau_workbook_in_repo() -> None:
    assert list(PROJECT_ROOT.glob("**/*.twbx")) == []
    assert list((PROJECT_ROOT / "tableau").glob("*.twb")) == []


def test_no_excel_workbook_in_repo() -> None:
    assert list((PROJECT_ROOT / "excel").glob("*.xlsx")) == []
    assert list((PROJECT_ROOT / "excel").glob("*.xlsm")) == []


def test_sql_directory_has_only_schema_files() -> None:
    sql_files = sorted((PROJECT_ROOT / "sql").glob("*.sql"))
    assert [path.name for path in sql_files] == SQL_SCHEMA_FILES


def test_no_week2_mart_build_sql_files() -> None:
    sql_dir = PROJECT_ROOT / "sql"
    extra = [p.name for p in sql_dir.glob("*.sql") if p.name not in SQL_SCHEMA_FILES]
    assert extra == []
