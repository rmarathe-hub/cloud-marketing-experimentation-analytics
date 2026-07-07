"""Hillstrom cleaning unit tests."""

from __future__ import annotations

import pandas as pd
import pytest

from clean_hillstrom_email import clean_hillstrom_email
from helpers import tiny_hillstrom_dataframe

pytestmark = [pytest.mark.unit, pytest.mark.cleaning]


def test_clean_hillstrom_treatment_mapping(tiny_hillstrom_df: pd.DataFrame) -> None:
    cleaned, _ = clean_hillstrom_email(tiny_hillstrom_df)
    mapping = dict(zip(cleaned["segment"], cleaned["treatment_group"]))
    assert mapping["No E-Mail"] == "control"
    assert mapping["Mens E-Mail"] == "mens_email"
    assert mapping["Womens E-Mail"] == "womens_email"
    assert "treatment_label" in cleaned.columns


def test_clean_hillstrom_aliases_and_validation() -> None:
    df = tiny_hillstrom_dataframe()
    invalid_rows = pd.DataFrame(
        [
            {
                "recency": 3,
                "history_segment": "1) $0 - $100",
                "history": 45.34,
                "mens": 0,
                "womens": 0,
                "zip_code": "Urban",
                "newbie": 1,
                "channel": "Phone",
                "segment": "Mens E-Mail",
                "visit": 0,
                "conversion": 0,
                "spend": -5.0,
            },
            {
                "recency": 4,
                "history_segment": "1) $0 - $100",
                "history": 55.0,
                "mens": 1,
                "womens": 0,
                "zip_code": "Urban",
                "newbie": 0,
                "channel": "Web",
                "segment": "Mens E-Mail",
                "visit": 2,
                "conversion": 0,
                "spend": 0.0,
            },
        ]
    )
    df = pd.concat([df, invalid_rows], ignore_index=True)
    cleaned, summary = clean_hillstrom_email(df)
    assert summary["dropped_invalid_visit"] == 1
    assert summary["dropped_invalid_spend"] == 1
    assert summary["output_rows"] == 4
    pd.testing.assert_series_equal(cleaned["converted"], cleaned["visit"], check_names=False)
    pd.testing.assert_series_equal(cleaned["revenue"], cleaned["spend"], check_names=False)
    assert (cleaned["revenue"] >= 0).all()


def test_clean_hillstrom_zip_code_std_fix() -> None:
    cleaned, summary = clean_hillstrom_email(tiny_hillstrom_dataframe())
    assert "Surburban" not in cleaned["zip_code_std"].tolist()
    assert summary["zip_code_typo_rows"] >= 1
    assert cleaned.loc[cleaned["zip_code"] == "Surburban", "zip_code_std"].iloc[0] == "Suburban"


def test_clean_hillstrom_summary_fields(tiny_hillstrom_df: pd.DataFrame) -> None:
    _, summary = clean_hillstrom_email(tiny_hillstrom_df)
    for key in [
        "input_rows",
        "output_rows",
        "rows_removed",
        "treatment_group_counts",
        "visit_rate",
        "conversion_rate",
    ]:
        assert key in summary


def test_clean_hillstrom_parquet_roundtrip(tmp_path, tiny_hillstrom_df) -> None:
    cleaned, _ = clean_hillstrom_email(tiny_hillstrom_df)
    parquet_path = tmp_path / "hillstrom_clean.parquet"
    cleaned.to_parquet(parquet_path, index=False)
    roundtrip = pd.read_parquet(parquet_path)
    assert len(roundtrip) == len(cleaned)
    assert "treatment_group" in roundtrip.columns
