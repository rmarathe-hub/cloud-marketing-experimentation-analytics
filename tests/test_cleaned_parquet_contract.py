"""Cleaned parquet contract tests."""

from __future__ import annotations

import pandas as pd
import pytest

from helpers import (
    AVAZU_CLEAN_PARQUET,
    HILLSTROM_CLEAN_PARQUET,
    assert_approx_percent,
    skip_if_missing,
)

pytestmark = [pytest.mark.data, pytest.mark.slow, pytest.mark.cleaning]

HILLSTROM_GROUP_COUNTS = {
    "womens_email": 21_387,
    "mens_email": 21_307,
    "control": 21_306,
}


@pytest.fixture(scope="module")
def avazu_clean_df() -> pd.DataFrame:
    skip_if_missing(AVAZU_CLEAN_PARQUET)
    return pd.read_parquet(AVAZU_CLEAN_PARQUET)


@pytest.fixture(scope="module")
def hillstrom_clean_df() -> pd.DataFrame:
    skip_if_missing(HILLSTROM_CLEAN_PARQUET)
    return pd.read_parquet(HILLSTROM_CLEAN_PARQUET)


def test_avazu_clean_exists() -> None:
    skip_if_missing(AVAZU_CLEAN_PARQUET)


def test_hillstrom_clean_exists() -> None:
    skip_if_missing(HILLSTROM_CLEAN_PARQUET)


def test_avazu_clean_shape_and_click_contract(avazu_clean_df: pd.DataFrame) -> None:
    assert len(avazu_clean_df) == 500_000
    assert len(avazu_clean_df.columns) == 36
    assert set(avazu_clean_df["click"].unique()).issubset({0, 1})
    assert int(avazu_clean_df["click"].sum()) == 82_037
    assert_approx_percent(avazu_clean_df["click"].mean() * 100, 16.41, tolerance=0.05)


def test_avazu_clean_date_and_hour_fields(avazu_clean_df: pd.DataFrame) -> None:
    assert "event_date" in avazu_clean_df.columns
    assert "event_hour" in avazu_clean_df.columns
    assert avazu_clean_df["event_hour"].between(0, 23).all()
    assert str(avazu_clean_df["event_date"].iloc[0]) == "2014-10-21"


def test_avazu_clean_unknown_flags(avazu_clean_df: pd.DataFrame) -> None:
    flag_cols = [c for c in avazu_clean_df.columns if c.startswith("flag_unknown_")]
    assert flag_cols
    expected = avazu_clean_df[flag_cols].any(axis=1)
    pd.testing.assert_series_equal(avazu_clean_df["flag_missing_fields"], expected, check_names=False)


@pytest.mark.parametrize(
    "column",
    ["id", "click", "event_date", "event_hour", "device_id", "app_id", "site_id", "flag_missing_fields"],
)
def test_avazu_clean_required_columns(column: str, avazu_clean_df: pd.DataFrame) -> None:
    assert column in avazu_clean_df.columns


def test_hillstrom_clean_shape_and_treatment_groups(hillstrom_clean_df: pd.DataFrame) -> None:
    assert len(hillstrom_clean_df) == 64_000
    assert len(hillstrom_clean_df.columns) == 19
    counts = hillstrom_clean_df["treatment_group"].value_counts().to_dict()
    for group, expected in HILLSTROM_GROUP_COUNTS.items():
        assert counts[group] == expected


def test_hillstrom_clean_aliases_and_validation(hillstrom_clean_df: pd.DataFrame) -> None:
    pd.testing.assert_series_equal(hillstrom_clean_df["converted"], hillstrom_clean_df["visit"], check_names=False)
    pd.testing.assert_series_equal(hillstrom_clean_df["revenue"], hillstrom_clean_df["spend"], check_names=False)
    assert hillstrom_clean_df["visit"].isin([0, 1]).all()
    assert hillstrom_clean_df["conversion"].isin([0, 1]).all()
    assert (hillstrom_clean_df["revenue"] >= 0).all()


def test_hillstrom_clean_zip_code_std(hillstrom_clean_df: pd.DataFrame) -> None:
    assert "Surburban" not in hillstrom_clean_df["zip_code_std"].astype(str).tolist()
    assert int(hillstrom_clean_df["flag_zip_code_typo"].sum()) == 28_776


@pytest.mark.parametrize(
    "column",
    ["treatment_group", "treatment_label", "converted", "revenue", "zip_code_std", "flag_zip_code_typo"],
)
def test_hillstrom_clean_required_columns(column: str, hillstrom_clean_df: pd.DataFrame) -> None:
    assert column in hillstrom_clean_df.columns
