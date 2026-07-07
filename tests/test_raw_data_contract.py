"""Real raw data contract tests."""

from __future__ import annotations

import pandas as pd
import pytest

from helpers import (
    AVAZU_RAW_CSV,
    HILLSTROM_RAW_CSV,
    assert_approx_percent,
    assert_approx_ratio,
    skip_if_missing,
)

pytestmark = [pytest.mark.data, pytest.mark.slow, pytest.mark.integration]

AVAZU_REQUIRED_COLUMNS = [
    "id",
    "click",
    "hour",
    "C1",
    "banner_pos",
    "site_id",
    "site_domain",
    "site_category",
    "app_id",
    "app_domain",
    "app_category",
    "device_id",
    "device_ip",
    "device_model",
    "device_type",
    "device_conn_type",
    "C14",
    "C15",
    "C16",
    "C17",
    "C18",
    "C19",
    "C20",
    "C21",
]

HILLSTROM_GROUP_COUNTS = {
    "Womens E-Mail": 21387,
    "Mens E-Mail": 21307,
    "No E-Mail": 21306,
}


@pytest.fixture(scope="module")
def avazu_raw_df() -> pd.DataFrame:
    skip_if_missing(AVAZU_RAW_CSV)
    return pd.read_csv(AVAZU_RAW_CSV, low_memory=False)


@pytest.fixture(scope="module")
def hillstrom_raw_df() -> pd.DataFrame:
    skip_if_missing(HILLSTROM_RAW_CSV)
    return pd.read_csv(HILLSTROM_RAW_CSV)


def test_avazu_raw_file_exists() -> None:
    skip_if_missing(AVAZU_RAW_CSV)


def test_hillstrom_raw_file_exists() -> None:
    skip_if_missing(HILLSTROM_RAW_CSV)


def test_avazu_row_count(avazu_raw_df: pd.DataFrame) -> None:
    assert len(avazu_raw_df) == 500_000


@pytest.mark.parametrize("column", AVAZU_REQUIRED_COLUMNS)
def test_avazu_required_columns(column: str, avazu_raw_df: pd.DataFrame) -> None:
    assert column in avazu_raw_df.columns


def test_avazu_click_count_and_ctr(avazu_raw_df: pd.DataFrame) -> None:
    clicks = pd.to_numeric(avazu_raw_df["click"], errors="coerce")
    valid = clicks.isin([0, 1])
    click_count = int(clicks[valid].sum())
    assert click_count == 82_037
    ctr = click_count / len(avazu_raw_df)
    assert_approx_percent(ctr * 100, 16.41, tolerance=0.05)


def test_avazu_date_sample(avazu_raw_df: pd.DataFrame) -> None:
    dates = pd.to_datetime(avazu_raw_df["hour"].astype(str), format="%y%m%d%H", errors="coerce")
    assert str(dates.min().date()) == "2014-10-21"
    assert str(dates.max().date()) == "2014-10-21"


def test_avazu_unique_entity_counts(avazu_raw_df: pd.DataFrame) -> None:
    assert avazu_raw_df["device_id"].nunique() == 41_413
    assert avazu_raw_df["app_id"].nunique() == 1_641
    assert avazu_raw_df["site_id"].nunique() == 1_704


def test_avazu_missing_values_zero(avazu_raw_df: pd.DataFrame) -> None:
    assert avazu_raw_df.isna().sum().sum() == 0


def test_avazu_click_binary(avazu_raw_df: pd.DataFrame) -> None:
    clicks = pd.to_numeric(avazu_raw_df["click"], errors="coerce")
    assert clicks.isin([0, 1]).all()


def test_hillstrom_row_count(hillstrom_raw_df: pd.DataFrame) -> None:
    assert len(hillstrom_raw_df) == 64_000


@pytest.mark.parametrize("segment,count", list(HILLSTROM_GROUP_COUNTS.items()))
def test_hillstrom_group_counts(segment: str, count: int, hillstrom_raw_df: pd.DataFrame) -> None:
    assert int((hillstrom_raw_df["segment"] == segment).sum()) == count


def test_hillstrom_visit_and_conversion_rates(hillstrom_raw_df: pd.DataFrame) -> None:
    visit_rate = hillstrom_raw_df["visit"].mean()
    conversion_rate = hillstrom_raw_df["conversion"].mean()
    assert_approx_percent(visit_rate * 100, 14.68, tolerance=0.05)
    assert_approx_percent(conversion_rate * 100, 0.90, tolerance=0.05)


def test_hillstrom_surburban_typo_present(hillstrom_raw_df: pd.DataFrame) -> None:
    assert (hillstrom_raw_df["zip_code"] == "Surburban").any()


def test_hillstrom_spend_nonnegative(hillstrom_raw_df: pd.DataFrame) -> None:
    assert (hillstrom_raw_df["spend"] >= 0).all()


def test_hillstrom_visit_conversion_binary(hillstrom_raw_df: pd.DataFrame) -> None:
    assert hillstrom_raw_df["visit"].isin([0, 1]).all()
    assert hillstrom_raw_df["conversion"].isin([0, 1]).all()
