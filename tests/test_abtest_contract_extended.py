"""Extended A/B test analysis contract tests."""

from __future__ import annotations

import pytest

import run_ab_test_analysis as ab_test

pytestmark = [pytest.mark.abtest, pytest.mark.unit]


def test_ab_test_module_exports_main_and_runner():
    assert hasattr(ab_test, "main")
    assert hasattr(ab_test, "run_ab_test_analysis")


def test_ab_test_uses_statsmodels_proportions_ztest():
    source = open(ab_test.__file__, encoding="utf-8").read()
    assert "proportions_ztest" in source or "statsmodels" in source


def test_ab_test_mart_table_constant():
    assert ab_test.MART_TABLE == "mart_ab_test_results"


@pytest.mark.parametrize(
    "field_name",
    [
        "absolute_lift",
        "relative_lift_pct",
        "incremental_revenue",
        "p_value",
        "ci_lower",
        "ci_upper",
        "statistically_significant",
    ],
)
def test_ab_test_mart_includes_statistical_fields(field_name: str):
    source = open(ab_test.__file__, encoding="utf-8").read()
    assert field_name in source


def test_ab_test_reads_from_stg_email_experiment():
    source = open(ab_test.__file__, encoding="utf-8").read()
    assert "stg_email_experiment" in source


def test_ab_test_writes_summary_json():
    source = open(ab_test.__file__, encoding="utf-8").read().lower()
    assert "ab_test_summary" in source or "summary_path" in source
