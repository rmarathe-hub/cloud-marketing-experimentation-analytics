"""cleaning_summary.json contract tests."""

from __future__ import annotations

import pandas as pd
import pytest

from helpers import CLEANING_SUMMARY, load_json, skip_if_missing
from paths import AVAZU_CLEAN_PARQUET, HILLSTROM_CLEAN_PARQUET

pytestmark = [pytest.mark.data, pytest.mark.slow, pytest.mark.cleaning]


@pytest.fixture(scope="module")
def cleaning_summary() -> dict:
    skip_if_missing(CLEANING_SUMMARY)
    return load_json(CLEANING_SUMMARY)


def test_cleaning_summary_exists() -> None:
    skip_if_missing(CLEANING_SUMMARY)


def test_cleaning_summary_schema(cleaning_summary: dict) -> None:
    assert "datasets" in cleaning_summary
    assert "avazu" in cleaning_summary["datasets"]
    assert "hillstrom" in cleaning_summary["datasets"]


def test_cleaning_summary_avazu_counts(cleaning_summary: dict) -> None:
    avazu = cleaning_summary["datasets"]["avazu"]
    assert avazu["input_rows"] == 500_000
    assert avazu["output_rows"] == 500_000
    assert avazu["rows_removed"] == 0


def test_cleaning_summary_hillstrom_counts(cleaning_summary: dict) -> None:
    hillstrom = cleaning_summary["datasets"]["hillstrom"]
    assert hillstrom["input_rows"] == 64_000
    assert hillstrom["output_rows"] == 64_000
    assert hillstrom["rows_removed"] == 0
    assert hillstrom["zip_code_typo_rows"] == 28_776


def test_cleaning_summary_matches_parquet_row_counts(cleaning_summary: dict) -> None:
    skip_if_missing(AVAZU_CLEAN_PARQUET)
    skip_if_missing(HILLSTROM_CLEAN_PARQUET)
    avazu_rows = len(pd.read_parquet(AVAZU_CLEAN_PARQUET))
    hillstrom_rows = len(pd.read_parquet(HILLSTROM_CLEAN_PARQUET))
    assert cleaning_summary["datasets"]["avazu"]["output_rows"] == avazu_rows
    assert cleaning_summary["datasets"]["hillstrom"]["output_rows"] == hillstrom_rows
