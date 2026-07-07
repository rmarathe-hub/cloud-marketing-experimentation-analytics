"""Avazu cleaning unit tests."""

from __future__ import annotations

import pandas as pd
import pytest

from clean_avazu_ads import clean_avazu_ads
from helpers import tiny_avazu_dataframe

pytestmark = [pytest.mark.unit, pytest.mark.cleaning]


def test_clean_avazu_standardizes_columns_and_dates(tiny_avazu_df: pd.DataFrame) -> None:
    cleaned, summary = clean_avazu_ads(tiny_avazu_df)
    assert "c1" in cleaned.columns
    assert "event_date" in cleaned.columns
    assert "event_hour" in cleaned.columns
    assert cleaned.loc[0, "event_hour"] == 8
    assert str(cleaned.loc[0, "event_date"]) == "2014-10-21"


def test_clean_avazu_removes_invalid_click_rows() -> None:
    cleaned, summary = clean_avazu_ads(tiny_avazu_dataframe())
    assert summary["dropped_invalid_click"] == 1
    assert summary["output_rows"] == 2
    assert set(cleaned["click"].unique()).issubset({0, 1})


def test_clean_avazu_unknown_flags() -> None:
    cleaned, _ = clean_avazu_ads(tiny_avazu_dataframe())
    assert bool(cleaned.loc[1, "flag_unknown_site_id"]) is True
    assert bool(cleaned.loc[1, "flag_unknown_device_type"]) is True
    assert cleaned["flag_missing_fields"].any()
    assert bool(cleaned.loc[0, "flag_missing_fields"]) is False


def test_clean_avazu_summary_fields(tiny_avazu_df: pd.DataFrame) -> None:
    _, summary = clean_avazu_ads(tiny_avazu_df)
    for key in ["input_rows", "output_rows", "rows_removed", "ctr", "date_range"]:
        assert key in summary


def test_clean_avazu_writes_parquet_roundtrip(tmp_path, tiny_avazu_df) -> None:
    cleaned, _ = clean_avazu_ads(tiny_avazu_df)
    parquet_path = tmp_path / "avazu_clean.parquet"
    cleaned.to_parquet(parquet_path, index=False)
    roundtrip = pd.read_parquet(parquet_path)
    assert len(roundtrip) == len(cleaned)
    assert "flag_missing_fields" in roundtrip.columns


@pytest.mark.parametrize(
    "flag_column",
    [
        "flag_unknown_site_id",
        "flag_unknown_app_id",
        "flag_unknown_device_id",
        "flag_missing_fields",
    ],
)
def test_clean_avazu_flag_columns_exist(flag_column, tiny_avazu_df) -> None:
    cleaned, _ = clean_avazu_ads(tiny_avazu_df)
    assert flag_column in cleaned.columns


def test_clean_avazu_flag_missing_fields_is_or_of_unknown_flags() -> None:
    cleaned, _ = clean_avazu_ads(tiny_avazu_dataframe())
    flag_cols = [c for c in cleaned.columns if c.startswith("flag_unknown_")]
    expected = cleaned[flag_cols].any(axis=1)
    pd.testing.assert_series_equal(cleaned["flag_missing_fields"], expected, check_names=False)
