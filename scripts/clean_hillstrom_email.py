#!/usr/bin/env python3
"""Clean Hillstrom email experiment data."""

from __future__ import annotations

import sys

import pandas as pd

from cleaning_utils import merge_cleaning_summary, to_snake_case
from paths import HILLSTROM_CLEAN_PARQUET, HILLSTROM_RAW_CSV, PROCESSED_DIR

SEGMENT_MAP = {
    "No E-Mail": "control",
    "Mens E-Mail": "mens_email",
    "Womens E-Mail": "womens_email",
}

TREATMENT_LABELS = {
    "control": "Control (No E-Mail)",
    "mens_email": "Mens E-Mail",
    "womens_email": "Womens E-Mail",
}

ZIP_CODE_MAP = {
    "Surburban": "Suburban",
    "Suburban": "Suburban",
    "Urban": "Urban",
    "Rural": "Rural",
}


def clean_hillstrom_email(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    input_rows = len(df)
    cleaned = df.copy()
    cleaned.columns = [to_snake_case(col) for col in cleaned.columns]

    cleaned["visit"] = pd.to_numeric(cleaned["visit"], errors="coerce")
    cleaned["conversion"] = pd.to_numeric(cleaned["conversion"], errors="coerce")
    cleaned["spend"] = pd.to_numeric(cleaned["spend"], errors="coerce")

    invalid_visit_mask = ~cleaned["visit"].isin([0, 1])
    invalid_conversion_mask = ~cleaned["conversion"].isin([0, 1])
    invalid_spend_mask = cleaned["spend"].isna() | (cleaned["spend"] < 0)

    dropped_invalid_visit = int(invalid_visit_mask.sum())
    dropped_invalid_conversion = int(invalid_conversion_mask.sum())
    dropped_invalid_spend = int(invalid_spend_mask.sum())

    invalid_mask = invalid_visit_mask | invalid_conversion_mask | invalid_spend_mask
    cleaned = cleaned.loc[~invalid_mask].copy()

    cleaned["visit"] = cleaned["visit"].astype("int8")
    cleaned["conversion"] = cleaned["conversion"].astype("int8")
    cleaned["spend"] = cleaned["spend"].astype("float64")
    cleaned["mens"] = cleaned["mens"].astype("int8")
    cleaned["womens"] = cleaned["womens"].astype("int8")
    cleaned["newbie"] = cleaned["newbie"].astype("int8")
    cleaned["recency"] = cleaned["recency"].astype("int16")
    cleaned["history"] = cleaned["history"].astype("float64")

    cleaned["treatment_group"] = cleaned["segment"].map(SEGMENT_MAP)
    unmapped_segments = cleaned["treatment_group"].isna()
    dropped_unmapped_segment = int(unmapped_segments.sum())
    cleaned = cleaned.loc[~unmapped_segments].copy()

    cleaned["treatment_label"] = cleaned["treatment_group"].map(TREATMENT_LABELS)
    cleaned["converted"] = cleaned["visit"]
    cleaned["revenue"] = cleaned["spend"]

    cleaned["zip_code_std"] = cleaned["zip_code"].map(ZIP_CODE_MAP)
    cleaned["flag_zip_code_typo"] = cleaned["zip_code"] != cleaned["zip_code_std"]
    zip_code_typo_rows = int(cleaned["flag_zip_code_typo"].sum())

    cleaned["flag_missing_fields"] = cleaned["zip_code_std"].isna()
    rows_with_unknown_fields = int(cleaned["flag_missing_fields"].sum())

    output_rows = len(cleaned)
    treatment_counts = cleaned["treatment_group"].value_counts().astype(int).to_dict()

    summary = {
        "dataset": "hillstrom_email_experiment",
        "input_file": str(HILLSTROM_RAW_CSV.name),
        "output_file": str(HILLSTROM_CLEAN_PARQUET.relative_to(PROCESSED_DIR.parent)),
        "input_rows": input_rows,
        "output_rows": output_rows,
        "rows_removed": input_rows - output_rows,
        "dropped_invalid_visit": dropped_invalid_visit,
        "dropped_invalid_conversion": dropped_invalid_conversion,
        "dropped_invalid_spend": dropped_invalid_spend,
        "dropped_unmapped_segment": dropped_unmapped_segment,
        "zip_code_typo_rows": zip_code_typo_rows,
        "rows_with_unknown_fields": rows_with_unknown_fields,
        "treatment_group_counts": treatment_counts,
        "visit_rate": round(float(cleaned["visit"].mean()), 6) if output_rows else 0.0,
        "conversion_rate": round(float(cleaned["conversion"].mean()), 6) if output_rows else 0.0,
        "revenue_mean": round(float(cleaned["revenue"].mean()), 4) if output_rows else 0.0,
        "columns": list(cleaned.columns),
    }
    return cleaned, summary


def main() -> int:
    if not HILLSTROM_RAW_CSV.exists():
        print(f"Missing raw Hillstrom file: {HILLSTROM_RAW_CSV}")
        print("Run scripts/download_or_import_data.py first.")
        return 1

    print(f"Loading {HILLSTROM_RAW_CSV}...")
    raw_df = pd.read_csv(HILLSTROM_RAW_CSV)

    print("Cleaning Hillstrom data...")
    cleaned_df, summary = clean_hillstrom_email(raw_df)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    cleaned_df.to_parquet(HILLSTROM_CLEAN_PARQUET, index=False)
    merge_cleaning_summary("hillstrom", summary)

    print(f"Wrote {HILLSTROM_CLEAN_PARQUET}")
    print(
        f"  Rows: {summary['input_rows']:,} -> {summary['output_rows']:,} "
        f"({summary['rows_removed']:,} removed)"
    )
    print(f"  Visit rate: {summary['visit_rate'] * 100:.4f}%")
    print(f"  Conversion rate: {summary['conversion_rate'] * 100:.4f}%")
    print(f"  Treatment groups: {summary['treatment_group_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
