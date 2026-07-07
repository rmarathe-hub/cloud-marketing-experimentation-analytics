"""Raw profiler unit tests."""

from __future__ import annotations

import pandas as pd
import pytest

from helpers import assert_approx_percent, tiny_avazu_dataframe, tiny_hillstrom_dataframe
from profile_raw_data import profile_avazu_dataframe, profile_hillstrom_dataframe, render_quality_report, write_profile_summary

pytestmark = [pytest.mark.unit, pytest.mark.profiling]


def test_profile_avazu_dataframe_metrics(tiny_avazu_df: pd.DataFrame) -> None:
    profile = profile_avazu_dataframe(tiny_avazu_df, "tiny_avazu.csv")
    assert profile["row_count"] == 2
    assert profile["click_distribution"]["click"] == 1
    assert profile["click_distribution"]["no_click"] == 1
    assert profile["ctr"] == 0.5
    assert profile["date_range"]["min_event_date"] == "2014-10-21"
    assert profile["unique_counts"]["device_id"] == 2


def test_profile_avazu_invalid_click_excluded(tiny_avazu_df: pd.DataFrame) -> None:
    profile = profile_avazu_dataframe(tiny_avazu_df, "tiny_avazu.csv")
    assert profile["row_count"] == 2
    assert profile["click_distribution"]["invalid"] == 0


def test_profile_avazu_invalid_hour_still_counts_rows_with_valid_clicks() -> None:
    df = tiny_avazu_dataframe()
    profile = profile_avazu_dataframe(df)
    assert profile["row_count"] == 2


def test_profile_hillstrom_dataframe_metrics(tiny_hillstrom_df: pd.DataFrame) -> None:
    profile = profile_hillstrom_dataframe(tiny_hillstrom_df, "tiny_hillstrom.csv")
    assert profile["row_count"] == 4
    assert profile["treatment_control_counts"]["No E-Mail"] == 1
    assert profile["visit_rate"] == 0.5
    assert profile["conversion_rate"] == 0.25
    assert "Surburban" in profile["zip_code_distribution"]


def test_profile_hillstrom_segment_metrics_present(tiny_hillstrom_df: pd.DataFrame) -> None:
    profile = profile_hillstrom_dataframe(tiny_hillstrom_df)
    assert len(profile["segment_metrics"]) == 3


def test_write_profile_summary_and_report(tmp_path, tiny_avazu_df, tiny_hillstrom_df) -> None:
    summary = {
        "generated_at": "2026-01-01T00:00:00+00:00",
        "datasets": {
            "avazu": profile_avazu_dataframe(tiny_avazu_df),
            "hillstrom": profile_hillstrom_dataframe(tiny_hillstrom_df),
        },
    }
    out = tmp_path / "raw_profile_summary.json"
    write_profile_summary(summary, out)
    assert out.exists()
    report = render_quality_report(summary)
    assert "Avazu" in report
    assert "Hillstrom" in report


@pytest.mark.parametrize(
    "field,expected",
    [
        ("ctr", 0.5),
        ("row_count", 2),
    ],
)
def test_profile_avazu_parametrized_fields(field, expected, tiny_avazu_df) -> None:
    profile = profile_avazu_dataframe(tiny_avazu_df)
    assert profile[field] == expected


def test_profile_hillstrom_visit_rate(tiny_hillstrom_df) -> None:
    profile = profile_hillstrom_dataframe(tiny_hillstrom_df)
    assert_approx_percent(profile["visit_rate_pct"], 50.0, tolerance=0.01)
