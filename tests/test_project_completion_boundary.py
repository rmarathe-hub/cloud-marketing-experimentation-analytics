"""Project completion boundary tests for Week 1 + Week 2 vs Phase 3."""

from __future__ import annotations

import re

import pytest

from helpers import (
    ALL_SCRIPTS,
    DOCS_DIR,
    EXCEL_WORKBOOK_SHEETS,
    MART_CSV_EXPORTS,
    PHASE3_FORBIDDEN_COMPLETE_PHRASES,
    PHASE3_FORBIDDEN_TRACKED_PATTERNS,
    PROJECT_ROOT,
    README_FORBIDDEN_COMPLETE_PHRASES,
    README_WEEK1_COMPLETE_PHRASES,
    README_WEEK2_COMPLETE_PHRASES,
    REQUIRED_DOCS,
    REQUIRED_ROOT_FILES,
    SQL_SCHEMA_FILES,
    VALIDATION_CHECK_NAMES,
    WEEK1_LOCKED,
    WEEK2_LOCKED,
    WEEK2_SCRIPTS_PENDING,
    git_tracked_files,
    read_text,
)

pytestmark = [pytest.mark.docs, pytest.mark.hygiene, pytest.mark.unit]

README = read_text(PROJECT_ROOT / "README.md")


@pytest.mark.parametrize("filename", REQUIRED_ROOT_FILES)
def test_required_root_file_exists(filename: str) -> None:
    assert (PROJECT_ROOT / filename).is_file()


@pytest.mark.parametrize("script_name", ALL_SCRIPTS)
def test_all_pipeline_script_exists(script_name: str) -> None:
    assert (PROJECT_ROOT / "scripts" / script_name).is_file()


@pytest.mark.parametrize("script_name", WEEK2_SCRIPTS_PENDING)
def test_no_pending_week2_scripts(script_name: str) -> None:
    assert not (PROJECT_ROOT / "scripts" / script_name).exists()


@pytest.mark.parametrize("doc_name", REQUIRED_DOCS)
def test_required_doc_exists(doc_name: str) -> None:
    assert (DOCS_DIR / doc_name).is_file()


@pytest.mark.parametrize("sql_file", SQL_SCHEMA_FILES)
def test_sql_schema_file_exists(sql_file: str) -> None:
    assert (PROJECT_ROOT / "sql" / sql_file).is_file()


@pytest.mark.parametrize("phrase", README_WEEK1_COMPLETE_PHRASES)
def test_readme_marks_week1_complete(phrase: str) -> None:
    assert phrase in README


@pytest.mark.parametrize("phrase", README_WEEK2_COMPLETE_PHRASES)
def test_readme_marks_week2_complete(phrase: str) -> None:
    assert phrase in README


@pytest.mark.parametrize("phrase", README_FORBIDDEN_COMPLETE_PHRASES)
def test_readme_does_not_mark_phase3_complete(phrase: str) -> None:
    assert phrase not in README


@pytest.mark.parametrize("phrase", PHASE3_FORBIDDEN_COMPLETE_PHRASES)
def test_readme_does_not_claim_phase3_phrases(phrase: str) -> None:
    assert phrase.lower() not in README.lower()


def test_readme_lists_tableau_pending() -> None:
    assert "Tableau dashboard | 🔲 Pending" in README


def test_readme_lists_excel_polish_pending() -> None:
    assert "Excel stakeholder workbook | 🔲 Pending" in README


def test_readme_lists_final_case_study_pending() -> None:
    assert "Final README case study | 🔲 Pending" in README


def test_readme_links_week1_and_week2_lock_docs() -> None:
    assert "week1_data_lock.md" in README
    assert "week2_analytics_lock.md" in README


def test_readme_includes_full_week2_pipeline_commands() -> None:
    for script in (
        "run_campaign_kpis.py",
        "run_funnel_segment_analysis.py",
        "run_ab_test_analysis.py",
        "run_ctr_forecast.py",
        "generate_recommendations.py",
        "export_dashboard_data.py",
        "generate_week2_analytics_lock.py",
    ):
        assert script in README


@pytest.mark.parametrize("pattern", PHASE3_FORBIDDEN_TRACKED_PATTERNS)
def test_phase3_deliverables_not_tracked(pattern: str) -> None:
    regex = re.compile(pattern)
    matches = [path for path in git_tracked_files() if regex.search(path)]
    assert matches == [], f"Tracked Phase 3 artifact(s): {matches}"


def test_no_tableau_workbook_tracked() -> None:
    tracked = git_tracked_files()
    assert not any(path.endswith(".twbx") or path.endswith(".twb") for path in tracked)


def test_validation_check_registry_length_matches_locked_count() -> None:
    assert len(VALIDATION_CHECK_NAMES) == WEEK1_LOCKED["validation_check_count"]


@pytest.mark.parametrize("check_name", VALIDATION_CHECK_NAMES)
def test_validation_check_name_is_documented_in_week2_lock(check_name: str) -> None:
    assert check_name in read_text(DOCS_DIR / "week2_analytics_lock.md")


@pytest.mark.parametrize("csv_name", MART_CSV_EXPORTS)
def test_mart_csv_name_documented_in_data_dictionary(csv_name: str) -> None:
    assert csv_name in read_text(DOCS_DIR / "data_dictionary.md")


@pytest.mark.parametrize("sheet_name", EXCEL_WORKBOOK_SHEETS)
def test_excel_sheet_name_documented_in_export_script(sheet_name: str) -> None:
    assert sheet_name in read_text(PROJECT_ROOT / "scripts" / "export_dashboard_data.py")


def test_week2_locked_recommendation_counts_in_lock_doc() -> None:
    lock = read_text(DOCS_DIR / "week2_analytics_lock.md")
    assert f"scale={WEEK2_LOCKED['recommendation_scale']}" in lock
    assert f"pause={WEEK2_LOCKED['recommendation_pause']}" in lock
    assert f"retest={WEEK2_LOCKED['recommendation_retest']}" in lock


def test_week1_locked_row_counts_in_week1_lock_doc() -> None:
    lock = read_text(DOCS_DIR / "week1_data_lock.md")
    assert f"{WEEK1_LOCKED['avazu_rows']:,}" in lock
    assert f"{WEEK1_LOCKED['hillstrom_rows']:,}" in lock


def test_week2_lock_doc_states_phase3_not_started() -> None:
    lock = read_text(DOCS_DIR / "week2_analytics_lock.md").lower()
    assert "phase 3 boundary" in lock
    assert "not started" in lock
    assert "tableau dashboard" in lock


def test_recommendations_doc_does_not_claim_tableau_complete() -> None:
    text = read_text(DOCS_DIR / "recommendations.md").lower()
    assert "tableau dashboard | ✅ complete" not in text


def test_executive_summary_mentions_phase3_pending() -> None:
    text = read_text(DOCS_DIR / "executive_summary.md").lower()
    assert "tableau" in text or "phase 3" in text or "pending" in text
