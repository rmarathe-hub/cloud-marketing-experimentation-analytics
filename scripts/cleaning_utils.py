"""Shared helpers for data cleaning scripts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from paths import CLEANING_SUMMARY, PROCESSED_DIR

UNKNOWN_STRINGS = {"", "nan", "null", "none", "unknown", "-1"}


def is_unknown_string(series: pd.Series) -> pd.Series:
    normalized = series.astype(str).str.strip().str.lower()
    return series.isna() | normalized.isin(UNKNOWN_STRINGS)


def is_unknown_numeric(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    return series.isna() | (numeric == -1)


def merge_cleaning_summary(dataset_name: str, dataset_summary: dict[str, Any]) -> dict[str, Any]:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    if CLEANING_SUMMARY.exists():
        summary = json.loads(CLEANING_SUMMARY.read_text())
    else:
        summary = {"generated_at": None, "datasets": {}}

    summary["generated_at"] = datetime.now(timezone.utc).isoformat()
    summary["datasets"][dataset_name] = dataset_summary
    CLEANING_SUMMARY.write_text(json.dumps(summary, indent=2))
    return summary


def to_snake_case(name: str) -> str:
    return name.strip().lower()
