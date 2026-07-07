#!/usr/bin/env python3
"""Generate the locked Week 1 data foundation documentation."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from paths import (
    CLEANING_SUMMARY,
    DATA_VALIDATION_SUMMARY,
    DOCS_DIR,
    DUCKDB_LOAD_SUMMARY,
    RAW_PROFILE_SUMMARY,
    S3_UPLOAD_SUMMARY,
    WEEK1_DATA_LOCK_DOC,
)

REQUIRED_SUMMARIES = (
    RAW_PROFILE_SUMMARY,
    CLEANING_SUMMARY,
    DUCKDB_LOAD_SUMMARY,
    DATA_VALIDATION_SUMMARY,
)

WEEK1_PIPELINE = [
    "download_or_import_data.py",
    "profile_raw_data.py",
    "clean_avazu_ads.py",
    "clean_hillstrom_email.py",
    "upload_to_s3.py",
    "create_duckdb_database.py",
    "load_to_duckdb.py",
    "validate_data.py",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_required_summaries() -> dict[str, dict[str, Any]]:
    missing = [str(path) for path in REQUIRED_SUMMARIES if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing required Week 1 summary files:\n  - "
            + "\n  - ".join(missing)
            + "\nRun the full Week 1 pipeline before generating the lock doc."
        )

    return {
        "profile": load_json(RAW_PROFILE_SUMMARY),
        "cleaning": load_json(CLEANING_SUMMARY),
        "load": load_json(DUCKDB_LOAD_SUMMARY),
        "validation": load_json(DATA_VALIDATION_SUMMARY),
        "s3": load_json(S3_UPLOAD_SUMMARY) if S3_UPLOAD_SUMMARY.exists() else None,
    }


def build_lock_document(summaries: dict[str, dict[str, Any]]) -> str:
    profile = summaries["profile"]["datasets"]
    cleaning = summaries["cleaning"]["datasets"]
    load = summaries["load"]
    validation = summaries["validation"]
    s3 = summaries["s3"]

    avazu_profile = profile["avazu"]
    hillstrom_profile = profile["hillstrom"]
    avazu_clean = cleaning["avazu"]
    hillstrom_clean = cleaning["hillstrom"]

    s3_section = (
        "S3 upload summary not found locally. Run `python scripts/upload_to_s3.py`."
    )
    if s3:
        uploaded = [
            f"- `{item['s3_key']}` ({item['size_mb']:.2f} MB)"
            for item in s3.get("uploads", [])
            if item.get("status") == "success"
        ]
        s3_section = "\n".join(
            [
                f"- Bucket: `{s3.get('bucket', 'configured-in-env')}`",
                f"- Uploaded files: {s3.get('uploaded_count', 0)}",
                *uploaded,
            ]
        )

    validation_lines = [
        f"- {check['check_name']}: {check['status']}"
        for check in validation.get("checks", [])
    ]

    load_lines = [
        f"- `{item['table_name']}`: {item['row_count']:,} rows ({item['status']})"
        for item in load.get("loads", [])
    ]

    pipeline_lines = "\n".join(
        f"{index}. `python scripts/{script}`"
        for index, script in enumerate(WEEK1_PIPELINE, start=1)
    )

    generated_at = datetime.now(timezone.utc).isoformat()

    return f"""# Week 1 Data Lock

**Status:** Locked  
**Generated:** {generated_at}  
**Scope:** Days 1–6 data foundation (no analytics marts)

This document freezes the verified Week 1 dataset statistics and pipeline outputs. Do not change locked values in downstream docs without re-running the full Week 1 pipeline and regenerating this file.

---

## Locked dataset statistics

### Avazu mobile ads

| Metric | Locked value |
|--------|--------------|
| Raw rows | {avazu_profile['row_count']:,} |
| Cleaned rows | {avazu_clean['output_rows']:,} |
| CTR | {avazu_clean['ctr'] * 100:.4f}% |
| Date range | {avazu_clean['date_range']['min_event_date']} to {avazu_clean['date_range']['max_event_date']} |
| Rows removed in cleaning | {avazu_clean['rows_removed']:,} |

### Hillstrom email experiment

| Metric | Locked value |
|--------|--------------|
| Raw rows | {hillstrom_profile['row_count']:,} |
| Cleaned rows | {hillstrom_clean['output_rows']:,} |
| Visit rate | {hillstrom_clean['visit_rate'] * 100:.4f}% |
| Conversion rate | {hillstrom_clean['conversion_rate'] * 100:.4f}% |
| Rows removed in cleaning | {hillstrom_clean['rows_removed']:,} |

### Hillstrom treatment groups (locked)

| Group | Recipients |
|-------|------------|
| control | {hillstrom_clean['treatment_group_counts']['control']:,} |
| mens_email | {hillstrom_clean['treatment_group_counts']['mens_email']:,} |
| womens_email | {hillstrom_clean['treatment_group_counts']['womens_email']:,} |

---

## Week 1 pipeline (frozen order)

{pipeline_lines}

Regenerate this lock after any upstream data change:

```bash
python scripts/generate_week1_data_lock.py
```

---

## Local artifacts (gitignored)

| Artifact | Purpose |
|----------|---------|
| `data/raw/avazu_train.csv` | Avazu source |
| `data/raw/hillstrom_email.csv` | Hillstrom source |
| `data/processed/avazu_clean.parquet` | Cleaned Avazu |
| `data/processed/hillstrom_clean.parquet` | Cleaned Hillstrom |
| `data/processed/raw_profile_summary.json` | Profiling output |
| `data/processed/cleaning_summary.json` | Cleaning output |
| `data/processed/marketing_analytics.duckdb` | DuckDB warehouse |
| `data/processed/duckdb_load_summary.json` | Load output |
| `data/processed/data_validation_summary.json` | Validation output |
| `data/processed/s3_upload_summary.json` | S3 upload output |

---

## DuckDB load status

Database: `{load.get('database_path', 'data/processed/marketing_analytics.duckdb')}`

{chr(10).join(load_lines)}

Mart tables remain empty until Week 2 analytics scripts run.

---

## Validation status

Validation success: **{validation.get('success', False)}**  
Checks passed: **{validation.get('passed_count', 0)} / {validation.get('passed_count', 0) + validation.get('failed_count', 0)}**

{chr(10).join(validation_lines)}

---

## S3 upload status

{s3_section}

---

## Change policy

1. Do not edit locked statistics manually in analytics docs.
2. Re-run the full Week 1 pipeline if source data or cleaning logic changes.
3. Regenerate this document with `generate_week1_data_lock.py`.
4. Re-run `pytest -q -m "not network and not slow"` before starting Week 2.

---

## Week 2 boundary

Week 1 ends here. The following are **not started**:

- Campaign KPI marts
- A/B test analysis scripts
- CTR forecasting
- Tableau dashboard
- Excel workbook

Proceed to Week 2 only after this lock document matches your local validation output.
"""


def generate_week1_data_lock(output_path: Path | None = None) -> Path:
    summaries = validate_required_summaries()
    if not summaries["validation"].get("success"):
        raise RuntimeError(
            "Validation summary indicates failures. "
            "Run `python scripts/validate_data.py` successfully before locking Week 1."
        )

    content = build_lock_document(summaries)
    target = output_path or WEEK1_DATA_LOCK_DOC
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def main() -> int:
    print("=" * 60)
    print("Week 1 data lock")
    print("=" * 60)

    try:
        output_path = generate_week1_data_lock()
        print(f"Wrote {output_path}")
        print("Week 1 data foundation is locked.")
        return 0
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"Lock generation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
