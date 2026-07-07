"""Extended recommendations generator contract tests."""

from __future__ import annotations

import pytest

import generate_recommendations as recommendations

pytestmark = [pytest.mark.recommendations, pytest.mark.unit]

DECISION_CONSTANTS = (
    ("DEFAULT_MIN_IMPRESSIONS", 1_000),
    ("CTR_SCALE_MULTIPLIER", 1.15),
    ("CTR_PAUSE_MULTIPLIER", 0.75),
    ("FORECAST_MAPE_RETEST_THRESHOLD", 100.0),
)


@pytest.mark.parametrize("constant_name,expected_value", DECISION_CONSTANTS)
def test_recommendation_threshold_constants(constant_name: str, expected_value: float):
    assert getattr(recommendations, constant_name) == expected_value


def test_recommendation_dataclass_exists():
    assert hasattr(recommendations, "Recommendation")


def test_build_recommendations_returns_list():
    payload = {
        "overall_ctr": 0.10,
        "impressions": 1000,
        "clicks": 100,
        "hourly_rows": [],
        "top_segments": [],
        "bottom_segments": [],
        "ab_results": [],
        "forecast": {"model_name": "moving_average_3", "mae": 1.0, "rmse": 1.0, "mape": 150.0},
    }
    recs = recommendations.build_recommendations(payload)
    assert isinstance(recs, list)


def test_recommendation_actions_are_scale_pause_or_retest():
    payload = {
        "overall_ctr": 0.10,
        "impressions": 10000,
        "clicks": 1000,
        "hourly_rows": [{"event_hour": 8, "impressions": 1000, "clicks": 200, "ctr": 0.20}],
        "top_segments": [
            {
                "device_type": 1,
                "app_category": "app_a",
                "site_category": "site_a",
                "banner_pos": 0,
                "impressions": 5000,
                "clicks": 1000,
                "ctr": 0.20,
                "click_share": 0.5,
            }
        ],
        "bottom_segments": [
            {
                "device_type": 1,
                "app_category": "app_b",
                "site_category": "site_b",
                "banner_pos": 1,
                "impressions": 5000,
                "clicks": 50,
                "ctr": 0.01,
                "click_share": 0.05,
            }
        ],
        "ab_results": [
            {
                "treatment_group": "mens_email",
                "treatment_label": "Mens",
                "recipients": 100,
                "conversions": 20,
                "conversion_rate": 0.20,
                "absolute_lift": 0.10,
                "relative_lift_pct": 100.0,
                "incremental_revenue": 100.0,
                "p_value": 0.01,
                "statistically_significant": True,
            }
        ],
        "forecast": {"model_name": "moving_average_3", "mae": 10.0, "rmse": 12.0, "mape": 150.0},
    }
    recs = recommendations.build_recommendations(payload)
    assert recs
    assert {item.action for item in recs}.issubset({"Scale", "Pause", "Retest"})


def test_executive_summary_builder_mentions_caveats():
    source = open(recommendations.__file__, encoding="utf-8").read().lower()
    assert "caveat" in source
    assert "phase 3" in source or "tableau" in source
