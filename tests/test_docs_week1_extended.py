"""Extended Week 1 documentation consistency tests."""

from __future__ import annotations

import pytest

from helpers import DOCS_DIR, PROJECT_ROOT, WEEK1_LOCKED, read_text

pytestmark = [pytest.mark.docs, pytest.mark.week1]

DOC_KEYWORDS = {
    "business_problem.md": [
        "stakeholder",
        "mobile ad",
        "email",
        "scale",
        "pause",
        "retest",
        "Tableau",
        "Excel",
        "real data",
    ],
    "metric_definitions.md": [
        "CTR",
        "impressions",
        "clicks",
        "conversion rate",
        "lift",
        "p-value",
        "confidence interval",
        "MAE",
        "RMSE",
        "MAPE",
        "forecast",
    ],
    "data_dictionary.md": [
        "Avazu",
        "Hillstrom",
        "event_date",
        "event_hour",
        "treatment_group",
        "converted",
        "revenue",
        "mart_campaign_kpis",
    ],
    "data_quality_report.md": [
        "500,000",
        "64,000",
        "16.4074",
        "Womens E-Mail",
        "Mens E-Mail",
        "No E-Mail",
        "visit rate",
        "treatment labels",
    ],
    "project_plan.md": [
        "Repo scaffold",
        "Load data",
        "Week 2",
        "Tableau",
        "Excel",
        "DuckDB",
    ],
    "cost_controls.md": [
        "S3",
        "budget",
        "Glue",
        "Lambda",
        "Redshift",
        "EC2",
        "credentials",
    ],
    "aws_s3_setup.md": [
        "block public access",
        "marketing-analytics",
        "least-privilege",
        "avazu_train.csv",
        "avazu_clean.parquet",
        "never commit",
    ],
    "duckdb_setup.md": [
        "01_raw_tables.sql",
        "load_to_duckdb.py",
        "validate_data.py",
        "mart_campaign_kpis",
        "Week 2",
        "gitignore",
    ],
    "week1_data_lock.md": [
        "Locked",
        "500,000",
        "64,000",
        "generate_week1_data_lock.py",
        "Week 2 boundary",
    ],
}


@pytest.mark.parametrize("doc_name,keywords", list(DOC_KEYWORDS.items()))
def test_doc_contains_week1_keywords(doc_name: str, keywords: list[str]) -> None:
    content = read_text(DOCS_DIR / doc_name).lower()
    for keyword in keywords:
        assert keyword.lower() in content, f"{doc_name} missing '{keyword}'"


@pytest.mark.parametrize(
    "forbidden_phrase",
    [
        "campaign kpi marts complete",
        "tableau dashboard complete",
        "excel workbook complete",
        "a/b test analysis complete",
    ],
)
def test_docs_do_not_claim_week2_complete(forbidden_phrase: str) -> None:
    for doc in DOCS_DIR.glob("*.md"):
        assert forbidden_phrase not in read_text(doc).lower()


def test_data_dictionary_mentions_locked_row_counts() -> None:
    content = read_text(DOCS_DIR / "data_dictionary.md")
    assert "500,000" in content or "500000" in content
    assert "64,000" in content or "64000" in content


def test_readme_links_week1_lock_doc() -> None:
    readme = read_text(PROJECT_ROOT / "README.md")
    assert "week1_data_lock.md" in readme


def test_week1_lock_values_match_data_quality_report() -> None:
    report = read_text(DOCS_DIR / "data_quality_report.md")
    assert f"{WEEK1_LOCKED['avazu_ctr_pct']:.4f}%" in report
    assert f"{WEEK1_LOCKED['hillstrom_visit_rate_pct']:.4f}%" in report or "14.6781" in report
