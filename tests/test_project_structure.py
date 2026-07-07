"""Project structure and Day 1 contract tests."""

from __future__ import annotations

import pytest

from helpers import (
    DOCS_DIR,
    PROJECT_ROOT,
    REQUIRED_DIRS,
    REQUIRED_DOCS,
    REQUIRED_ROOT_FILES,
    REQUIRED_SCRIPTS,
    read_text,
)

pytestmark = [pytest.mark.unit, pytest.mark.hygiene]


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


def test_readme_has_project_title() -> None:
    readme = read_text(PROJECT_ROOT / "README.md")
    assert "Cloud Marketing Experimentation" in readme


@pytest.mark.parametrize(
    "keyword",
    ["Avazu", "Hillstrom", "AWS S3", "DuckDB", "Tableau", "Excel"],
)
def test_readme_mentions_core_stack(keyword: str) -> None:
    assert keyword in read_text(PROJECT_ROOT / "README.md")


def test_readme_status_shows_days_1_to_6_complete() -> None:
    readme = read_text(PROJECT_ROOT / "README.md")
    assert "Repo scaffold + business framing | ✅ Complete" in readme
    assert "Dataset acquisition + profiling | ✅ Complete" in readme
    assert "Cleaning pipeline | ✅ Complete" in readme
    assert "AWS S3 setup + upload | ✅ Complete" in readme
    assert "DuckDB warehouse setup | ✅ Complete" in readme
    assert "DuckDB load + validation | ✅ Complete" in readme


def test_readme_status_shows_week1_complete() -> None:
    readme = read_text(PROJECT_ROOT / "README.md")
    assert "Week 1 tests + docs lock | ✅ Complete" in readme
    assert "Campaign KPI marts | ✅ Complete" in readme
    assert "Funnel + segment analysis | ✅ Complete" in readme
    assert "A/B test analysis | 🔲 Pending" in readme


def test_readme_business_question_present() -> None:
    readme = read_text(PROJECT_ROOT / "README.md")
    assert "scale, pause, or retest" in readme.lower() or "scale / pause / retest" in readme
