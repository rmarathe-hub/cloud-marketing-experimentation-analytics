"""Documentation consistency tests."""

from __future__ import annotations

import pytest

from helpers import DOCS_DIR, read_text

pytestmark = pytest.mark.docs


@pytest.mark.parametrize(
    "doc_name,required_terms",
    [
        (
            "business_problem.md",
            [
                "stakeholder",
                "mobile ad",
                "email",
                "scale",
                "pause",
                "retest",
                "Tableau",
                "Excel",
                "A/B",
                "forecast",
                "AWS",
                "S3",
                "DuckDB",
            ],
        ),
        (
            "metric_definitions.md",
            [
                "CTR",
                "impressions",
                "clicks",
                "conversion rate",
                "lift",
                "p-value",
                "confidence interval",
                "MAPE",
                "MAE",
                "RMSE",
                "forecast",
                "recommendation",
            ],
        ),
        (
            "data_dictionary.md",
            [
                "Avazu",
                "Hillstrom",
                "500,000",
                "64,000",
                "event_date",
                "event_hour",
                "treatment_group",
                "visit",
                "conversion",
                "spend",
                "Suburban",
            ],
        ),
        (
            "data_quality_report.md",
            [
                "500,000",
                "64,000",
                "16.4074%",
                "Womens E-Mail",
                "Mens E-Mail",
                "No E-Mail",
                "visit rate",
                "conversion rate",
                "treatment labels",
            ],
        ),
        (
            "project_plan.md",
            [
                "Repo scaffold",
                "Dataset acquisition",
                "Cleaning pipeline",
                "| 4 |",
                "S3",
                "DuckDB",
                "Tableau",
                "Excel",
            ],
        ),
        (
            "cost_controls.md",
            [
                "S3",
                "budget",
                "Glue",
                "Lambda",
                "Redshift",
                "EC2",
                ".env",
                "credentials",
            ],
        ),
        (
            "aws_s3_setup.md",
            [
                "block public access",
                "never commit",
                "marketing-analytics",
                "least-privilege",
                "budget",
                "glue",
                "lambda",
                "ec2",
                "redshift",
                "athena",
            ],
        ),
        (
            "duckdb_setup.md",
            [
                "duckdb",
                "day 6",
                "raw_avazu_ads",
                "stg_ad_events",
                "mart_campaign_kpis",
                "gitignore",
                "glue",
                "lambda",
                "redshift",
                "athena",
            ],
        ),
    ],
)
def test_doc_contains_required_terms(doc_name: str, required_terms: list[str]) -> None:
    content = read_text(DOCS_DIR / doc_name).lower()
    for term in required_terms:
        assert term.lower() in content, f"{doc_name} missing '{term}'"
