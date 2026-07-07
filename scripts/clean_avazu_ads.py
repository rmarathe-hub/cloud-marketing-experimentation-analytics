#!/usr/bin/env python3
"""Clean Avazu mobile ad click data."""

from __future__ import annotations

import sys

import pandas as pd

from cleaning_utils import is_unknown_numeric, is_unknown_string, merge_cleaning_summary, to_snake_case
from paths import AVAZU_CLEAN_PARQUET, AVAZU_RAW_CSV, PROCESSED_DIR

FLAG_COLUMNS = [
    "site_id",
    "site_domain",
    "site_category",
    "app_id",
    "app_domain",
    "app_category",
    "device_id",
    "device_model",
    "device_type",
]


def clean_avazu_ads(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    input_rows = len(df)
    cleaned = df.copy()
    cleaned.columns = [to_snake_case(col) for col in cleaned.columns]

    cleaned["click"] = pd.to_numeric(cleaned["click"], errors="coerce")
    invalid_click_mask = ~cleaned["click"].isin([0, 1])
    dropped_invalid_click = int(invalid_click_mask.sum())
    cleaned = cleaned.loc[~invalid_click_mask].copy()
    cleaned["click"] = cleaned["click"].astype("int8")

    hour_text = cleaned["hour"].astype(str)
    event_ts = pd.to_datetime(hour_text, format="%y%m%d%H", errors="coerce")
    invalid_hour_mask = event_ts.isna()
    dropped_invalid_hour = int(invalid_hour_mask.sum())
    cleaned = cleaned.loc[~invalid_hour_mask].copy()
    event_ts = event_ts.loc[~invalid_hour_mask]

    cleaned["event_date"] = event_ts.dt.date
    cleaned["event_hour"] = event_ts.dt.hour.astype("int8")
    cleaned["hour"] = hour_text.loc[~invalid_hour_mask].astype("int64")

    unknown_flags: dict[str, int] = {}
    for column in FLAG_COLUMNS:
        if column not in cleaned.columns:
            continue
        if column == "device_type":
            flag = is_unknown_numeric(cleaned[column])
        else:
            flag = is_unknown_string(cleaned[column])
        flag_name = f"flag_unknown_{column}"
        cleaned[flag_name] = flag
        unknown_flags[column] = int(flag.sum())

    flag_cols = [col for col in cleaned.columns if col.startswith("flag_unknown_")]
    cleaned["flag_missing_fields"] = cleaned[flag_cols].any(axis=1)
    rows_with_unknown_fields = int(cleaned["flag_missing_fields"].sum())

    numeric_cols = ["banner_pos", "device_conn_type", "c14", "c15", "c16", "c17", "c18", "c19", "c20", "c21"]
    for column in numeric_cols:
        if column in cleaned.columns:
            cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")

    cleaned["id"] = cleaned["id"].astype(str)

    output_rows = len(cleaned)
    summary = {
        "dataset": "avazu_mobile_ads",
        "input_file": str(AVAZU_RAW_CSV.name),
        "output_file": str(AVAZU_CLEAN_PARQUET.relative_to(PROCESSED_DIR.parent)),
        "input_rows": input_rows,
        "output_rows": output_rows,
        "rows_removed": input_rows - output_rows,
        "dropped_invalid_click": dropped_invalid_click,
        "dropped_invalid_hour": dropped_invalid_hour,
        "rows_with_unknown_fields": rows_with_unknown_fields,
        "unknown_field_counts": unknown_flags,
        "ctr": round(float(cleaned["click"].mean()), 6) if output_rows else 0.0,
        "date_range": {
            "min_event_date": str(cleaned["event_date"].min()) if output_rows else None,
            "max_event_date": str(cleaned["event_date"].max()) if output_rows else None,
            "distinct_days": int(cleaned["event_date"].nunique()) if output_rows else 0,
        },
        "columns": list(cleaned.columns),
    }
    return cleaned, summary


def main() -> int:
    if not AVAZU_RAW_CSV.exists():
        print(f"Missing raw Avazu file: {AVAZU_RAW_CSV}")
        print("Run scripts/download_or_import_data.py first.")
        return 1

    print(f"Loading {AVAZU_RAW_CSV}...")
    raw_df = pd.read_csv(AVAZU_RAW_CSV, low_memory=False)

    print("Cleaning Avazu data...")
    cleaned_df, summary = clean_avazu_ads(raw_df)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    cleaned_df.to_parquet(AVAZU_CLEAN_PARQUET, index=False)
    merge_cleaning_summary("avazu", summary)

    print(f"Wrote {AVAZU_CLEAN_PARQUET}")
    print(
        f"  Rows: {summary['input_rows']:,} -> {summary['output_rows']:,} "
        f"({summary['rows_removed']:,} removed)"
    )
    print(f"  CTR: {summary['ctr'] * 100:.4f}%")
    print(f"  Rows with unknown field flags: {summary['rows_with_unknown_fields']:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
