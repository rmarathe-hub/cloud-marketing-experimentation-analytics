"""Data reproducibility and stability tests."""

from __future__ import annotations

import pandas as pd
import pytest

from clean_avazu_ads import clean_avazu_ads
from clean_hillstrom_email import clean_hillstrom_email
from helpers import tiny_avazu_dataframe, tiny_hillstrom_dataframe

pytestmark = [pytest.mark.unit, pytest.mark.cleaning]


def test_clean_avazu_is_reproducible() -> None:
    df = tiny_avazu_dataframe()
    cleaned_one, summary_one = clean_avazu_ads(df.copy())
    cleaned_two, summary_two = clean_avazu_ads(df.copy())
    assert summary_one == summary_two
    pd.testing.assert_frame_equal(cleaned_one, cleaned_two)


def test_clean_hillstrom_is_reproducible() -> None:
    df = tiny_hillstrom_dataframe()
    cleaned_one, summary_one = clean_hillstrom_email(df.copy())
    cleaned_two, summary_two = clean_hillstrom_email(df.copy())
    assert summary_one == summary_two
    pd.testing.assert_frame_equal(cleaned_one, cleaned_two)


def test_clean_avazu_column_order_is_stable() -> None:
    df = tiny_avazu_dataframe()
    cleaned_one, _ = clean_avazu_ads(df.copy())
    cleaned_two, _ = clean_avazu_ads(df.copy())
    assert list(cleaned_one.columns) == list(cleaned_two.columns)


def test_clean_hillstrom_summary_keys_are_stable() -> None:
    _, summary = clean_hillstrom_email(tiny_hillstrom_dataframe())
    expected_keys = {
        "dataset",
        "input_file",
        "output_file",
        "input_rows",
        "output_rows",
        "rows_removed",
        "dropped_invalid_visit",
        "dropped_invalid_conversion",
        "dropped_invalid_spend",
        "dropped_unmapped_segment",
        "zip_code_typo_rows",
        "rows_with_unknown_fields",
        "treatment_group_counts",
        "visit_rate",
        "conversion_rate",
        "revenue_mean",
        "columns",
    }
    assert expected_keys.issubset(set(summary.keys()))
