"""Phase 3 boundary tests across documentation."""

from __future__ import annotations

import pytest

from helpers import (
    DOCS_DIR,
    PHASE3_FORBIDDEN_COMPLETE_PHRASES,
    PROJECT_ROOT,
    assert_no_phase3_claims,
    read_text,
)

pytestmark = [pytest.mark.docs, pytest.mark.unit]

DOC_FILES = sorted(path.name for path in DOCS_DIR.glob("*.md"))


@pytest.mark.parametrize("doc_name", DOC_FILES)
def test_doc_does_not_claim_tableau_dashboard_complete(doc_name: str) -> None:
    assert_no_phase3_claims(read_text(DOCS_DIR / doc_name), doc_name)


@pytest.mark.parametrize("doc_name", DOC_FILES)
@pytest.mark.parametrize("phrase", PHASE3_FORBIDDEN_COMPLETE_PHRASES)
def test_doc_does_not_contain_forbidden_phase3_phrase(doc_name: str, phrase: str) -> None:
    assert phrase.lower() not in read_text(DOCS_DIR / doc_name).lower()


def test_ab_test_methodology_mentions_converted_equals_visit() -> None:
    text = read_text(DOCS_DIR / "ab_test_methodology.md").lower()
    assert "visit" in text
    assert "converted" in text or "conversion" in text


def test_forecast_methodology_mentions_single_day_caveat() -> None:
    text = read_text(DOCS_DIR / "forecast_methodology.md").lower()
    assert "mape" in text
    assert "single" in text or "holdout" in text or "day" in text


def test_metric_definitions_covers_week2_metrics() -> None:
    text = read_text(DOCS_DIR / "metric_definitions.md").lower()
    for term in ("ctr", "lift", "p-value", "mape", "click share", "incremental revenue"):
        assert term in text


def test_data_dictionary_lists_export_files() -> None:
    text = read_text(DOCS_DIR / "data_dictionary.md")
    for csv_name in (
        "campaign_kpis.csv",
        "ctr_trends.csv",
        "segment_performance.csv",
        "ab_test_results.csv",
        "forecast_results.csv",
        "recommendation_matrix.csv",
    ):
        assert csv_name in text


def test_duckdb_setup_covers_week2_pipeline() -> None:
    text = read_text(DOCS_DIR / "duckdb_setup.md").lower()
    for script in (
        "run_campaign_kpis.py",
        "run_funnel_segment_analysis.py",
        "run_ab_test_analysis.py",
        "run_ctr_forecast.py",
        "generate_recommendations.py",
        "export_dashboard_data.py",
        "generate_week2_analytics_lock.py",
    ):
        assert script in text


def test_project_plan_does_not_mark_tableau_complete() -> None:
    text = read_text(DOCS_DIR / "project_plan.md")
    assert "Tableau dashboard | ✅ Complete" not in text


def test_readme_does_not_claim_resume_docs_exist() -> None:
    readme = read_text(PROJECT_ROOT / "README.md").lower()
    assert "resume bullets complete" not in readme
    assert "interview prep complete" not in readme
