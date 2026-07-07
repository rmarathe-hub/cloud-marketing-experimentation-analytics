"""Final portfolio completion tests (Days 20–21)."""

from __future__ import annotations

import pytest

from helpers import (
    ALL_SCRIPTS,
    EXCEL_SCREENSHOT_FILES,
    README_CASE_STUDY_COMPLETE_PHRASES,
    README_EXCEL_COMPLETE_PHRASES,
    README_FINAL_TESTS_COMPLETE_PHRASES,
    README_PORTFOLIO_COMPLETE_PHRASES,
    README_TABLEAU_COMPLETE_PHRASES,
    REQUIRED_DOCS,
    TABLEAU_SCREENSHOT_FILES,
    VALIDATION_CHECK_NAMES,
    read_text,
)
from paths import DOCS_DIR, PROJECT_ROOT

pytestmark = [pytest.mark.unit, pytest.mark.docs, pytest.mark.portfolio, pytest.mark.hygiene]

README = read_text(PROJECT_ROOT / "README.md")
PROJECT_PLAN = read_text(DOCS_DIR / "project_plan.md")
PORTFOLIO_COMPLETION = read_text(DOCS_DIR / "portfolio_completion.md")


@pytest.mark.parametrize("doc_name", [
    "portfolio_completion.md",
    "resume_bullets.md",
    "interview_prep.md",
    "linkedin_summary.md",
])
def test_portfolio_doc_exists(doc_name: str) -> None:
    assert (DOCS_DIR / doc_name).is_file()


def test_all_required_docs_include_portfolio_docs() -> None:
    for doc_name in (
        "portfolio_completion.md",
        "resume_bullets.md",
        "interview_prep.md",
        "linkedin_summary.md",
    ):
        assert doc_name in REQUIRED_DOCS


def test_readme_marks_all_phases_complete() -> None:
    for phrases in (
        README_TABLEAU_COMPLETE_PHRASES,
        README_EXCEL_COMPLETE_PHRASES,
        README_CASE_STUDY_COMPLETE_PHRASES,
        README_FINAL_TESTS_COMPLETE_PHRASES,
        README_PORTFOLIO_COMPLETE_PHRASES,
    ):
        for phrase in phrases:
            assert phrase in README


def test_readme_links_portfolio_and_interview_docs() -> None:
    for doc in (
        "portfolio_completion.md",
        "resume_bullets.md",
        "interview_prep.md",
        "linkedin_summary.md",
    ):
        assert doc in README


def test_project_plan_marks_all_deliverables_complete() -> None:
    assert "All phases complete" in PROJECT_PLAN or "complete (Days 1–21)" in PROJECT_PLAN
    assert "- [x]" in PROJECT_PLAN
    assert "- [ ]" not in PROJECT_PLAN


def test_portfolio_completion_doc_lists_validation_commands() -> None:
    assert "pytest -q" in PORTFOLIO_COMPLETION
    assert "portfolio" in PORTFOLIO_COMPLETION.lower()


def test_portfolio_completion_doc_lists_locked_metrics() -> None:
    assert "500,000" in PORTFOLIO_COMPLETION
    assert "16.41%" in PORTFOLIO_COMPLETION
    assert "25.25%" in PORTFOLIO_COMPLETION


def test_resume_bullets_contain_locked_metrics() -> None:
    resume = read_text(DOCS_DIR / "resume_bullets.md")
    assert "500K" in resume or "500,000" in resume
    assert "7.66" in resume
    assert "DuckDB" in resume


def test_interview_prep_covers_ab_test_and_forecast_caveat() -> None:
    prep = read_text(DOCS_DIR / "interview_prep.md").lower()
    assert "a/b" in prep or "ab test" in prep
    assert "mape" in prep
    assert "single-day" in prep or "single day" in prep


def test_linkedin_summary_mentions_stack() -> None:
    linkedin = read_text(DOCS_DIR / "linkedin_summary.md")
    assert "DuckDB" in linkedin
    assert "Tableau" in linkedin


@pytest.mark.parametrize("filename", TABLEAU_SCREENSHOT_FILES)
def test_tableau_screenshots_present_for_portfolio(filename: str) -> None:
    path = PROJECT_ROOT / "tableau" / "screenshots" / filename
    assert path.is_file(), f"Missing Tableau screenshot: {filename}"


@pytest.mark.parametrize("filename", EXCEL_SCREENSHOT_FILES)
def test_excel_screenshots_present_for_portfolio(filename: str) -> None:
    path = PROJECT_ROOT / "excel" / "screenshots" / filename
    assert path.is_file(), f"Missing Excel screenshot: {filename}"


def test_script_inventory_is_complete() -> None:
    assert len(ALL_SCRIPTS) == 20


def test_validation_registry_matches_locked_count() -> None:
    assert len(VALIDATION_CHECK_NAMES) == 25


def test_executive_summary_no_longer_claims_phase3_pending() -> None:
    text = read_text(DOCS_DIR / "executive_summary.md").lower()
    assert "still pending" not in text
    assert "screenshot" in text or "complete" in text


def test_week2_lock_doc_lists_portfolio_completion() -> None:
    lock = read_text(DOCS_DIR / "week2_analytics_lock.md")
    assert "portfolio_completion.md" in lock
    assert "resume_bullets.md" in lock
