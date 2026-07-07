"""cleaning_utils tests."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from cleaning_utils import is_unknown_numeric, is_unknown_string, merge_cleaning_summary, to_snake_case

pytestmark = [pytest.mark.unit, pytest.mark.cleaning]


@pytest.mark.parametrize(
    "value,expected",
    [
        ("", True),
        ("  ", True),
        ("-1", True),
        ("unknown", True),
        ("Unknown", True),
        (None, True),
        ("valid_id", False),
        ("site_a", False),
    ],
)
def test_is_unknown_string(value, expected) -> None:
    series = pd.Series([value])
    assert bool(is_unknown_string(series).iloc[0]) is expected


@pytest.mark.parametrize(
    "value,expected",
    [
        (-1, True),
        (0, False),
        (1, False),
        (None, True),
    ],
)
def test_is_unknown_numeric(value, expected) -> None:
    series = pd.Series([value])
    assert bool(is_unknown_numeric(series).iloc[0]) is expected


def test_to_snake_case() -> None:
    assert to_snake_case("C1") == "c1"
    assert to_snake_case(" Banner_Pos ") == "banner_pos"


def test_merge_cleaning_summary_writes_and_merges(tmp_path: Path) -> None:
    summary_path = tmp_path / "cleaning_summary.json"
    avazu_summary = {"dataset": "avazu", "output_rows": 10}
    hillstrom_summary = {"dataset": "hillstrom", "output_rows": 4}

    merged = merge_cleaning_summary("avazu", avazu_summary, summary_path=summary_path)
    assert merged["datasets"]["avazu"]["output_rows"] == 10

    merged = merge_cleaning_summary("hillstrom", hillstrom_summary, summary_path=summary_path)
    payload = json.loads(summary_path.read_text())
    assert payload["datasets"]["avazu"]["output_rows"] == 10
    assert payload["datasets"]["hillstrom"]["output_rows"] == 4
    assert payload["generated_at"] is not None


def test_merge_cleaning_summary_handles_missing_existing_file(tmp_path: Path) -> None:
    summary_path = tmp_path / "new_cleaning_summary.json"
    result = merge_cleaning_summary("avazu", {"output_rows": 1}, summary_path=summary_path)
    assert summary_path.exists()
    assert "datasets" in result
