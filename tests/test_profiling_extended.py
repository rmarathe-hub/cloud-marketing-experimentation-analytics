"""Extended profiling tests on tiny controlled inputs."""

from __future__ import annotations

import pandas as pd
import pytest

from helpers import HILLSTROM_RAW_SEGMENTS, tiny_avazu_dataframe, tiny_hillstrom_dataframe
from profile_raw_data import profile_avazu_dataframe, profile_hillstrom_dataframe

pytestmark = [pytest.mark.profiling, pytest.mark.unit, pytest.mark.week1]


def test_profile_avazu_tiny_row_count():
    profile = profile_avazu_dataframe(tiny_avazu_dataframe())
    assert profile["row_count"] == 2  # invalid click row excluded


def test_profile_avazu_tiny_ctr():
    profile = profile_avazu_dataframe(tiny_avazu_dataframe())
    assert profile["click_distribution"]["click"] == 1
    assert profile["click_distribution"]["no_click"] == 1
    assert profile["ctr"] == 0.5


def test_profile_avazu_tiny_date_range():
    profile = profile_avazu_dataframe(tiny_avazu_dataframe())
    assert profile["date_range"]["min_event_date"] == "2014-10-21"


@pytest.mark.parametrize("field", ["row_count", "ctr", "ctr_pct", "columns", "unique_counts"])
def test_profile_avazu_required_fields(field: str):
    assert field in profile_avazu_dataframe(tiny_avazu_dataframe())


def test_profile_hillstrom_tiny_row_count():
    profile = profile_hillstrom_dataframe(tiny_hillstrom_dataframe())
    assert profile["row_count"] == 4


def test_profile_hillstrom_tiny_visit_rate():
    profile = profile_hillstrom_dataframe(tiny_hillstrom_dataframe())
    assert 0 < profile["visit_rate"] < 1


@pytest.mark.parametrize("segment", HILLSTROM_RAW_SEGMENTS)
def test_profile_hillstrom_detects_raw_segments(segment: str):
    profile = profile_hillstrom_dataframe(tiny_hillstrom_dataframe())
    assert segment in profile["treatment_control_counts"]


def test_profile_hillstrom_detects_surburban_typo_count():
    profile = profile_hillstrom_dataframe(tiny_hillstrom_dataframe())
    assert profile["zip_code_distribution"]["Surburban"] >= 1


def test_profile_missing_avazu_column_raises():
    df = tiny_avazu_dataframe().drop(columns=["click"])
    with pytest.raises(KeyError):
        profile_avazu_dataframe(df)


def test_profile_missing_hillstrom_visit_column_uses_fallback():
    df = tiny_hillstrom_dataframe().drop(columns=["visit"])
    profile = profile_hillstrom_dataframe(df)
    assert profile["row_count"] == len(df)
