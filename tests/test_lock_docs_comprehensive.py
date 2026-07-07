"""Comprehensive lock document contract tests."""

from __future__ import annotations

import pytest

from helpers import DOCS_DIR, WEEK1_LOCKED, WEEK2_LOCKED, read_text

pytestmark = [pytest.mark.docs, pytest.mark.week1, pytest.mark.week2]

WEEK1_LOCK_REQUIRED = [
    "Status:** Locked",
    "500,000",
    "64,000",
    "16.4074%",
    "14.6781%",
    "0.9031%",
    "control",
    "mens_email",
    "womens_email",
    "week2_analytics_lock.md",
    "generate_week1_data_lock.py",
]

WEEK2_LOCK_REQUIRED = [
    "Status:** Locked",
    "16.4074%",
    "25.25%",
    "68,033",
    "7.66%",
    "4.52%",
    "moving_average_3",
    "314.4%",
    "scale=6",
    "pause=3",
    "retest=1",
    "mart_device_app_performance",
    "recommendation_matrix.csv",
    "Phase 3 boundary",
    "generate_week2_analytics_lock.py",
]

LOCK_FORBIDDEN_ARTIFACTS = [
    "/tmp/pytest",
    "/private/var/folders",
    "pytest-of-",
]


@pytest.mark.parametrize("term", WEEK1_LOCK_REQUIRED)
def test_week1_lock_contains_required_term(term: str):
    assert term in read_text(DOCS_DIR / "week1_data_lock.md")


@pytest.mark.parametrize("term", WEEK2_LOCK_REQUIRED)
def test_week2_lock_contains_required_term(term: str):
    assert term in read_text(DOCS_DIR / "week2_analytics_lock.md")


@pytest.mark.parametrize("term", LOCK_FORBIDDEN_ARTIFACTS)
def test_week1_lock_has_no_test_artifacts(term: str):
    assert term not in read_text(DOCS_DIR / "week1_data_lock.md")


@pytest.mark.parametrize("term", LOCK_FORBIDDEN_ARTIFACTS)
def test_week2_lock_has_no_test_artifacts(term: str):
    assert term not in read_text(DOCS_DIR / "week2_analytics_lock.md")


@pytest.mark.parametrize(
    "mart_name,row_key",
    [
        ("mart_campaign_kpis", "campaign_kpi_rows"),
        ("mart_ctr_trends", "ctr_trend_rows"),
        ("mart_device_app_performance", "segment_performance_rows"),
        ("mart_ab_test_results", "ab_test_result_rows"),
        ("mart_forecast_inputs", "forecast_input_rows"),
        ("mart_forecast_results", "forecast_result_rows"),
    ],
)
def test_week2_lock_lists_mart_row_counts(mart_name: str, row_key: str):
    lock = read_text(DOCS_DIR / "week2_analytics_lock.md")
    assert mart_name in lock
    assert str(WEEK2_LOCKED[row_key]) in lock


def test_week1_lock_references_week2_marts_populated():
    lock = read_text(DOCS_DIR / "week1_data_lock.md").lower()
    assert "week2_analytics_lock.md" in lock
    assert "mart" in lock


def test_week2_lock_validation_count_matches_locked_constant():
    lock = read_text(DOCS_DIR / "week2_analytics_lock.md")
    assert str(WEEK1_LOCKED["validation_check_count"]) in lock
