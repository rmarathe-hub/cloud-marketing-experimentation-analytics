"""Smoke pipeline tests without network or real data."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from clean_avazu_ads import clean_avazu_ads
from clean_hillstrom_email import clean_hillstrom_email
from cleaning_utils import merge_cleaning_summary
from helpers import write_tiny_avazu_csv, write_tiny_hillstrom_csv
from profile_raw_data import profile_avazu_dataframe, profile_hillstrom_dataframe, write_profile_summary

pytestmark = [pytest.mark.smoke, pytest.mark.integration]


def test_smoke_profile_clean_summarize_pipeline(tmp_path: Path) -> None:
    raw_dir = tmp_path / "data" / "raw"
    processed_dir = tmp_path / "data" / "processed"
    raw_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)

    avazu_raw = write_tiny_avazu_csv(raw_dir / "avazu_train.csv")
    hillstrom_raw = write_tiny_hillstrom_csv(raw_dir / "hillstrom_email.csv")

    avazu_df = pd.read_csv(avazu_raw)
    hillstrom_df = pd.read_csv(hillstrom_raw)

    profile = {
        "generated_at": "test",
        "datasets": {
            "avazu": profile_avazu_dataframe(avazu_df),
            "hillstrom": profile_hillstrom_dataframe(hillstrom_df),
        },
    }
    profile_path = processed_dir / "raw_profile_summary.json"
    write_profile_summary(profile, profile_path)
    assert profile_path.exists()

    avazu_clean, avazu_summary = clean_avazu_ads(avazu_df)
    hillstrom_clean, hillstrom_summary = clean_hillstrom_email(hillstrom_df)

    avazu_parquet = processed_dir / "avazu_clean.parquet"
    hillstrom_parquet = processed_dir / "hillstrom_clean.parquet"
    avazu_clean.to_parquet(avazu_parquet, index=False)
    hillstrom_clean.to_parquet(hillstrom_parquet, index=False)

    summary_path = processed_dir / "cleaning_summary.json"
    merge_cleaning_summary("avazu", avazu_summary, summary_path=summary_path)
    merge_cleaning_summary("hillstrom", hillstrom_summary, summary_path=summary_path)

    payload = json.loads(summary_path.read_text())
    assert payload["datasets"]["avazu"]["output_rows"] == avazu_summary["output_rows"]
    assert payload["datasets"]["hillstrom"]["output_rows"] == hillstrom_summary["output_rows"]
    assert len(pd.read_parquet(avazu_parquet)) == avazu_summary["output_rows"]
    assert len(pd.read_parquet(hillstrom_parquet)) == hillstrom_summary["output_rows"]

    # Raw files should remain untouched by cleaning functions.
    assert len(pd.read_csv(avazu_raw)) == len(avazu_df)
    assert len(pd.read_csv(hillstrom_raw)) == len(hillstrom_df)
