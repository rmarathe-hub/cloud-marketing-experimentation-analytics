"""Week 2 analytics lock document and generator contract tests."""

from __future__ import annotations

import json

import pytest

import generate_week2_analytics_lock as week2_lock
from helpers import WEEK2_LOCKED, read_text
from paths import WEEK2_ANALYTICS_LOCK_DOC

pytestmark = [pytest.mark.week2, pytest.mark.docs, pytest.mark.unit]

LOCK_REQUIRED_STRINGS = [
    "Status:** Locked",
    "16.4074%",
    "25.25%",
    "mens_email",
    "womens_email",
    "moving_average_3",
    "314.4%",
    "recommendation_matrix.csv",
    "generate_week2_analytics_lock.py",
    "Phase 3 boundary",
    "Tableau dashboard",
]

LOCK_FORBIDDEN_STRINGS = [
    "/tmp/pytest",
    "/private/var/folders",
    "pytest-of-",
]


@pytest.mark.parametrize("term", LOCK_REQUIRED_STRINGS)
def test_week2_lock_doc_contains_required_term(term: str):
    assert term in read_text(WEEK2_ANALYTICS_LOCK_DOC)


@pytest.mark.parametrize("term", LOCK_FORBIDDEN_STRINGS)
def test_week2_lock_doc_does_not_contain_test_artifacts(term: str):
    assert term not in read_text(WEEK2_ANALYTICS_LOCK_DOC)


def test_generate_week2_lock_module_has_main():
    assert hasattr(week2_lock, "main")
    assert hasattr(week2_lock, "generate_week2_analytics_lock")


def test_generate_week2_lock_fails_without_summaries(tmp_path, monkeypatch):
    monkeypatch.setattr(week2_lock, "CAMPAIGN_KPI_SUMMARY", tmp_path / "missing_campaign.json")
    monkeypatch.setattr(week2_lock, "FUNNEL_SEGMENT_SUMMARY", tmp_path / "missing_funnel.json")
    monkeypatch.setattr(week2_lock, "AB_TEST_SUMMARY", tmp_path / "missing_ab.json")
    monkeypatch.setattr(week2_lock, "FORECAST_SUMMARY", tmp_path / "missing_forecast.json")
    monkeypatch.setattr(week2_lock, "RECOMMENDATIONS_SUMMARY", tmp_path / "missing_rec.json")
    monkeypatch.setattr(week2_lock, "EXPORT_DASHBOARD_SUMMARY", tmp_path / "missing_export.json")
    monkeypatch.setattr(week2_lock, "DATA_VALIDATION_SUMMARY", tmp_path / "missing_validation.json")
    with pytest.raises(FileNotFoundError):
        week2_lock.generate_week2_analytics_lock(output_path=tmp_path / "lock.md")


def test_locked_week2_constants_match_document():
    content = read_text(WEEK2_ANALYTICS_LOCK_DOC)
    assert f"scale={WEEK2_LOCKED['recommendation_scale']}" in content
    assert f"pause={WEEK2_LOCKED['recommendation_pause']}" in content
    assert f"retest={WEEK2_LOCKED['recommendation_retest']}" in content
    assert str(WEEK2_LOCKED["segment_performance_rows"]) in content
    assert WEEK2_LOCKED["forecast_model"] in content
