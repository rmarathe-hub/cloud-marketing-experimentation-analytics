"""raw_profile_summary.json contract tests."""

from __future__ import annotations

import pytest

from helpers import (
    RAW_PROFILE_SUMMARY,
    assert_approx_percent,
    assert_approx_ratio,
    load_json,
    read_text,
    skip_if_missing,
)

pytestmark = [pytest.mark.data, pytest.mark.slow, pytest.mark.profiling]


@pytest.fixture(scope="module")
def profile_summary() -> dict:
    skip_if_missing(RAW_PROFILE_SUMMARY)
    return load_json(RAW_PROFILE_SUMMARY)


def test_profile_summary_exists() -> None:
    skip_if_missing(RAW_PROFILE_SUMMARY)


def test_profile_summary_has_datasets(profile_summary: dict) -> None:
    assert "datasets" in profile_summary
    assert "avazu" in profile_summary["datasets"]
    assert "hillstrom" in profile_summary["datasets"]


def test_profile_summary_avazu_metrics(profile_summary: dict) -> None:
    avazu = profile_summary["datasets"]["avazu"]
    assert avazu["row_count"] == 500_000
    assert avazu["click_distribution"]["click"] == 82_037
    assert_approx_percent(avazu["ctr_pct"], 16.41, tolerance=0.05)
    assert avazu["unique_counts"]["device_id"] == 41_413
    assert avazu["unique_counts"]["app_id"] == 1_641
    assert avazu["unique_counts"]["site_id"] == 1_704
    assert avazu["missing_values"] == {}


def test_profile_summary_hillstrom_metrics(profile_summary: dict) -> None:
    hillstrom = profile_summary["datasets"]["hillstrom"]
    assert hillstrom["row_count"] == 64_000
    assert hillstrom["treatment_control_counts"]["Womens E-Mail"] == 21_387
    assert hillstrom["treatment_control_counts"]["Mens E-Mail"] == 21_307
    assert hillstrom["treatment_control_counts"]["No E-Mail"] == 21_306
    assert_approx_percent(hillstrom["visit_rate_pct"], 14.68, tolerance=0.05)
    assert_approx_percent(hillstrom["conversion_rate_pct"], 0.90, tolerance=0.05)


def test_profile_summary_consistent_with_quality_report(profile_summary: dict) -> None:
    from helpers import DOCS_DIR

    report = read_text(DOCS_DIR / "data_quality_report.md")
    assert "500,000" in report
    assert "64,000" in report
    assert "16.4074%" in report or "16.41" in report
