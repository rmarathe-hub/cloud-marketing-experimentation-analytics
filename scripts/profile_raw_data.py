#!/usr/bin/env python3
"""Profile raw Avazu and Hillstrom datasets."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from paths import (
    AVAZU_RAW_CSV,
    DOCS_DIR,
    HILLSTROM_RAW_CSV,
    PROJECT_ROOT,
    PROCESSED_DIR,
    RAW_PROFILE_SUMMARY,
)


def _missing_summary(df: pd.DataFrame) -> dict:
    missing = df.isna().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    return {
        col: {"count": int(missing[col]), "pct": float(missing_pct[col])}
        for col in df.columns
        if missing[col] > 0
    }


def _distribution_summary(series: pd.Series, bins: int = 10) -> dict:
    clean = series.dropna()
    if clean.empty:
        return {"min": None, "max": None, "mean": None, "median": None}

    return {
        "min": float(clean.min()),
        "max": float(clean.max()),
        "mean": round(float(clean.mean()), 4),
        "median": float(clean.median()),
        "std": round(float(clean.std()), 4) if len(clean) > 1 else 0.0,
    }


def profile_avazu_dataframe(df: pd.DataFrame, source_file: str = "avazu_train.csv") -> dict:
    df = df[pd.to_numeric(df["click"], errors="coerce").isin([0, 1])].copy()
    clicks = pd.to_numeric(df["click"], errors="coerce")
    impressions = len(df)
    click_count = int(clicks.fillna(0).sum())
    ctr = click_count / impressions if impressions else 0.0

    hour_series = df["hour"].astype(str)
    event_dates = pd.to_datetime(hour_series, format="%y%m%d%H", errors="coerce")

    return {
        "dataset": "avazu_mobile_ads",
        "file": source_file,
        "row_count": impressions,
        "column_count": len(df.columns),
        "columns": list(df.columns),
        "date_range": {
            "min_event_date": str(event_dates.min().date()) if event_dates.notna().any() else None,
            "max_event_date": str(event_dates.max().date()) if event_dates.notna().any() else None,
            "distinct_days": int(event_dates.dt.date.nunique()),
        },
        "missing_values": _missing_summary(df),
        "click_distribution": {
            "no_click": int((clicks == 0).sum()),
            "click": int((clicks == 1).sum()),
            "invalid": int(clicks.isna().sum() + (~clicks.isin([0, 1]) & clicks.notna()).sum()),
        },
        "ctr": round(ctr, 6),
        "ctr_pct": round(ctr * 100, 4),
        "unique_counts": {
            "device_id": int(df["device_id"].nunique()),
            "device_type": int(df["device_type"].nunique()),
            "app_id": int(df["app_id"].nunique()),
            "app_category": int(df["app_category"].nunique()),
            "site_id": int(df["site_id"].nunique()),
            "site_category": int(df["site_category"].nunique()),
            "banner_pos": int(df["banner_pos"].nunique()),
        },
        "top_device_types": (
            df["device_type"].astype(str).value_counts().head(5).astype(int).to_dict()
        ),
        "top_app_categories": (
            df["app_category"].astype(str).value_counts().head(5).astype(int).to_dict()
        ),
        "top_site_categories": (
            df["site_category"].astype(str).value_counts().head(5).astype(int).to_dict()
        ),
    }


def profile_avazu(path: Path) -> dict:
    df = pd.read_csv(path, low_memory=False)
    return profile_avazu_dataframe(df, str(path.relative_to(PROJECT_ROOT)))


def profile_hillstrom_dataframe(df: pd.DataFrame, source_file: str = "hillstrom_email.csv") -> dict:
    if "segment" in df.columns:
        treatment_col = "segment"
    elif "treatment" in df.columns:
        treatment_col = "treatment"
    else:
        treatment_col = df.columns[-2]

    conversion_col = "visit" if "visit" in df.columns else "conversion"
    purchase_col = "conversion" if "conversion" in df.columns else conversion_col
    revenue_col = "spend" if "spend" in df.columns else "revenue"

    visits = pd.to_numeric(df[conversion_col], errors="coerce").fillna(0)
    conversions = pd.to_numeric(df[purchase_col], errors="coerce").fillna(0)
    revenue = pd.to_numeric(df[revenue_col], errors="coerce").fillna(0)
    recipients = len(df)
    visit_count = int(visits.sum())
    conversion_count = int(conversions.sum())
    visit_rate = visit_count / recipients if recipients else 0.0
    conversion_rate = conversion_count / recipients if recipients else 0.0

    treatment_counts = df[treatment_col].astype(str).value_counts().astype(int).to_dict()

    segment_metrics = []
    for segment, group in df.groupby(treatment_col):
        group_visits = pd.to_numeric(group[conversion_col], errors="coerce").fillna(0)
        group_conversions = pd.to_numeric(group[purchase_col], errors="coerce").fillna(0)
        group_revenue = pd.to_numeric(group[revenue_col], errors="coerce").fillna(0)
        n = len(group)
        segment_metrics.append(
            {
                "segment": str(segment),
                "recipients": n,
                "visits": int(group_visits.sum()),
                "visit_rate": round(float(group_visits.sum() / n), 6) if n else 0.0,
                "conversions": int(group_conversions.sum()),
                "conversion_rate": round(float(group_conversions.sum() / n), 6) if n else 0.0,
                "total_revenue": round(float(group_revenue.sum()), 2),
                "revenue_per_customer": round(float(group_revenue.sum() / n), 4) if n else 0.0,
            }
        )

    return {
        "dataset": "hillstrom_email_experiment",
        "file": source_file,
        "row_count": recipients,
        "column_count": len(df.columns),
        "columns": list(df.columns),
        "missing_values": _missing_summary(df),
        "treatment_control_counts": treatment_counts,
        "visit_rate": round(visit_rate, 6),
        "visit_rate_pct": round(visit_rate * 100, 4),
        "conversion_rate": round(conversion_rate, 6),
        "conversion_rate_pct": round(conversion_rate * 100, 4),
        "visit_distribution": {
            "no_visit": int((visits == 0).sum()),
            "visit": int((visits == 1).sum()),
        },
        "conversion_distribution": {
            "no_conversion": int((conversions == 0).sum()),
            "conversion": int((conversions == 1).sum()),
        },
        "revenue_distribution": _distribution_summary(revenue),
        "segment_metrics": segment_metrics,
        "zip_code_distribution": (
            df["zip_code"].astype(str).value_counts().astype(int).to_dict()
            if "zip_code" in df.columns
            else {}
        ),
        "channel_distribution": (
            df["channel"].astype(str).value_counts().astype(int).to_dict()
            if "channel" in df.columns
            else {}
        ),
    }


def profile_hillstrom(path: Path) -> dict:
    df = pd.read_csv(path)
    return profile_hillstrom_dataframe(df, str(path.relative_to(PROJECT_ROOT)))


def write_profile_summary(summary: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2))


def render_quality_report(summary: dict) -> str:
    avazu = summary["datasets"]["avazu"]
    hillstrom = summary["datasets"]["hillstrom"]

    lines = [
        "# Data Quality Report",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "## Summary",
        "",
        "| Dataset | Rows | Key Metric |",
        "|---------|------|------------|",
        f"| Avazu mobile ads | {avazu['row_count']:,} | CTR: {avazu['ctr_pct']:.4f}% |",
        (
            f"| Hillstrom email experiment | {hillstrom['row_count']:,} | "
            f"Visit rate: {hillstrom['visit_rate_pct']:.4f}% |"
        ),
        "",
        "## Avazu — Mobile Ad Click Data",
        "",
        f"- **File:** `{avazu['file']}`",
        f"- **Rows:** {avazu['row_count']:,}",
        f"- **Date range:** {avazu['date_range']['min_event_date']} to "
        f"{avazu['date_range']['max_event_date']} "
        f"({avazu['date_range']['distinct_days']} distinct days)",
        f"- **CTR:** {avazu['ctr_pct']:.4f}% ({avazu['click_distribution']['click']:,} clicks / "
        f"{avazu['row_count']:,} impressions)",
        "",
        "### Click distribution",
        "",
        "| Outcome | Count |",
        "|---------|-------|",
        f"| No click (0) | {avazu['click_distribution']['no_click']:,} |",
        f"| Click (1) | {avazu['click_distribution']['click']:,} |",
        f"| Invalid | {avazu['click_distribution']['invalid']:,} |",
        "",
        "### Unique entity counts",
        "",
        "| Entity | Unique values |",
        "|--------|---------------|",
    ]

    for entity, count in avazu["unique_counts"].items():
        lines.append(f"| {entity} | {count:,} |")

    lines.extend(
        [
            "",
            "### Missing values",
            "",
        ]
    )

    if avazu["missing_values"]:
        lines.append("| Column | Missing | % |")
        lines.append("|--------|---------|---|")
        for col, stats in avazu["missing_values"].items():
            lines.append(f"| {col} | {stats['count']:,} | {stats['pct']:.2f}% |")
    else:
        lines.append("No missing values detected.")

    lines.extend(
        [
            "",
            "## Hillstrom — Email A/B Experiment",
            "",
            f"- **File:** `{hillstrom['file']}`",
            f"- **Rows:** {hillstrom['row_count']:,}",
            f"- **Overall visit rate:** {hillstrom['visit_rate_pct']:.4f}%",
            f"- **Overall conversion rate:** {hillstrom['conversion_rate_pct']:.4f}%",
            "",
            "### Treatment / control counts",
            "",
            "| Segment | Recipients |",
            "|---------|------------|",
        ]
    )

    for segment, count in hillstrom["treatment_control_counts"].items():
        lines.append(f"| {segment} | {count:,} |")

    lines.extend(
        [
            "",
            "### Segment performance (raw)",
            "",
            "| Segment | Recipients | Visits | Visit rate | Conversions | Conversion rate | Revenue/customer |",
            "|---------|------------|--------|------------|-------------|-----------------|------------------|",
        ]
    )

    for segment in hillstrom["segment_metrics"]:
        lines.append(
            f"| {segment['segment']} | {segment['recipients']:,} | "
            f"{segment['visits']:,} | {segment['visit_rate']*100:.4f}% | "
            f"{segment['conversions']:,} | {segment['conversion_rate']*100:.4f}% | "
            f"${segment['revenue_per_customer']:.2f} |"
        )

    rev = hillstrom["revenue_distribution"]
    lines.extend(
        [
            "",
            "### Revenue distribution",
            "",
            f"- Min: ${rev['min']:.2f}",
            f"- Max: ${rev['max']:.2f}",
            f"- Mean: ${rev['mean']:.2f}",
            f"- Median: ${rev['median']:.2f}",
            "",
            "### Missing values",
            "",
        ]
    )

    if hillstrom["missing_values"]:
        lines.append("| Column | Missing | % |")
        lines.append("|--------|---------|---|")
        for col, stats in hillstrom["missing_values"].items():
            lines.append(f"| {col} | {stats['count']:,} | {stats['pct']:.2f}% |")
    else:
        lines.append("No missing values detected.")

    lines.extend(
        [
            "",
            "## Initial quality notes",
            "",
            "- Avazu `click` should be validated as binary (0/1) during cleaning.",
            "- Avazu `hour` field will be parsed into `event_date` and `event_hour`.",
            "- Hillstrom experiment groups should map to standardized treatment labels.",
            "- Revenue/spend contains many zero values; analyze lift with and without buyers.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    missing = [
        path
        for path in (AVAZU_RAW_CSV, HILLSTROM_RAW_CSV)
        if not path.exists()
    ]
    if missing:
        print("Missing raw data files. Run download_or_import_data.py first:")
        for path in missing:
            print(f"  - {path}")
        return 1

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("Profiling Avazu data...")
    avazu_profile = profile_avazu(AVAZU_RAW_CSV)

    print("Profiling Hillstrom data...")
    hillstrom_profile = profile_hillstrom(HILLSTROM_RAW_CSV)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "datasets": {
            "avazu": avazu_profile,
            "hillstrom": hillstrom_profile,
        },
    }

    write_profile_summary(summary, RAW_PROFILE_SUMMARY)
    print(f"Wrote {RAW_PROFILE_SUMMARY}")

    report_path = DOCS_DIR / "data_quality_report.md"
    report_path.write_text(render_quality_report(summary))
    print(f"Wrote {report_path}")

    print("\nProfile highlights:")
    print(
        f"  Avazu:     {avazu_profile['row_count']:,} rows | "
        f"CTR {avazu_profile['ctr_pct']:.4f}%"
    )
    print(
        f"  Hillstrom: {hillstrom_profile['row_count']:,} rows | "
        f"Visit {hillstrom_profile['visit_rate_pct']:.4f}% | "
        f"Conversion {hillstrom_profile['conversion_rate_pct']:.4f}%"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
