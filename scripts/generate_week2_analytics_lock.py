#!/usr/bin/env python3
"""Generate the locked Week 2 marketing analytics documentation."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from paths import (
    AB_TEST_SUMMARY,
    CAMPAIGN_KPI_SUMMARY,
    DATA_VALIDATION_SUMMARY,
    EXPORT_DASHBOARD_SUMMARY,
    FORECAST_SUMMARY,
    FUNNEL_SEGMENT_SUMMARY,
    RECOMMENDATIONS_SUMMARY,
    WEEK2_ANALYTICS_LOCK_DOC,
)

REQUIRED_SUMMARIES = (
    CAMPAIGN_KPI_SUMMARY,
    FUNNEL_SEGMENT_SUMMARY,
    AB_TEST_SUMMARY,
    FORECAST_SUMMARY,
    RECOMMENDATIONS_SUMMARY,
    EXPORT_DASHBOARD_SUMMARY,
    DATA_VALIDATION_SUMMARY,
)

WEEK2_PIPELINE = [
    "run_campaign_kpis.py",
    "run_funnel_segment_analysis.py",
    "run_ab_test_analysis.py",
    "run_ctr_forecast.py",
    "generate_recommendations.py",
    "export_dashboard_data.py",
    "validate_data.py",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_required_summaries() -> dict[str, dict[str, Any]]:
    missing = [str(path) for path in REQUIRED_SUMMARIES if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing required Week 2 summary files:\n  - "
            + "\n  - ".join(missing)
            + "\nRun the full Week 2 analytics pipeline before generating the lock doc."
        )

    return {
        "campaign": load_json(CAMPAIGN_KPI_SUMMARY),
        "funnel": load_json(FUNNEL_SEGMENT_SUMMARY),
        "ab_test": load_json(AB_TEST_SUMMARY),
        "forecast": load_json(FORECAST_SUMMARY),
        "recommendations": load_json(RECOMMENDATIONS_SUMMARY),
        "exports": load_json(EXPORT_DASHBOARD_SUMMARY),
        "validation": load_json(DATA_VALIDATION_SUMMARY),
    }


def _safe_database_path(summary: dict[str, Any]) -> str:
    path = str(summary.get("database_path", "data/processed/marketing_analytics.duckdb"))
    if any(token in path for token in ("/tmp/", "/pytest-", "/private/var/")):
        return "data/processed/marketing_analytics.duckdb"
    return path


def _find_treatment(ab_test: dict[str, Any], group: str) -> dict[str, Any]:
    for result in ab_test.get("results", []):
        if result.get("treatment_group") == group:
            return result
    raise KeyError(f"Treatment group not found in A/B summary: {group}")


def build_lock_document(summaries: dict[str, dict[str, Any]]) -> str:
    campaign = summaries["campaign"]
    funnel = summaries["funnel"]
    ab_test = summaries["ab_test"]
    forecast = summaries["forecast"]
    recommendations = summaries["recommendations"]
    exports = summaries["exports"]
    validation = summaries["validation"]

    ctr_trends = funnel["marts"]["mart_ctr_trends"]
    segment_mart = funnel["marts"]["mart_device_app_performance"]
    top_segment = funnel["segment_rankings"]["top_by_ctr"][0]
    control = _find_treatment(ab_test, "control")
    mens = _find_treatment(ab_test, "mens_email")
    womens = _find_treatment(ab_test, "womens_email")

    mart_lines = [
        f"- `mart_campaign_kpis`: {campaign['mart_row_count']:,} rows",
        f"- `mart_ctr_trends`: {ctr_trends['row_count']:,} rows",
        f"- `mart_device_app_performance`: {segment_mart['row_count']:,} rows",
        f"- `mart_ab_test_results`: {ab_test['mart_row_count']:,} rows",
        f"- `mart_forecast_inputs`: {forecast['input_row_count']:,} rows",
        f"- `mart_forecast_results`: {forecast['results_row_count']:,} rows",
    ]

    export_lines = [
        f"- `{item['csv_name']}`: {item['row_count']:,} rows ({item['description']})"
        for item in exports.get("csv_exports", [])
    ]

    validation_lines = [
        f"- {check['check_name']}: {check['status']}"
        for check in validation.get("checks", [])
    ]

    pipeline_lines = "\n".join(
        f"{index}. `python scripts/{script}`"
        for index, script in enumerate(WEEK2_PIPELINE, start=1)
    )

    generated_at = datetime.now(timezone.utc).isoformat()

    return f"""# Week 2 Analytics Lock

**Status:** Locked  
**Generated:** {generated_at}  
**Scope:** Days 8–13 marketing analytics, recommendations, and BI exports

This document freezes verified Week 2 mart statistics, experiment outcomes, forecast metrics, recommendations, and export inventory. Do not change locked values in downstream docs without re-running the full Week 2 pipeline and regenerating this file.

---

## Locked headline metrics

| Metric | Locked value |
|--------|--------------|
| Portfolio CTR | {campaign['overall_ctr'] * 100:.4f}% |
| Impressions | {campaign['total_impressions']:,} |
| Clicks | {campaign['total_clicks']:,} |
| Top segment CTR | {top_segment['ctr'] * 100:.2f}% on {top_segment['impressions']:,} impressions |
| Mens E-Mail absolute lift | {mens['absolute_lift'] * 100:.2f}% |
| Womens E-Mail absolute lift | {womens['absolute_lift'] * 100:.2f}% |
| Forecast model | {forecast['selected_model']} |
| Forecast MAPE | {forecast['selected_metrics']['mape']:.1f}% |
| Recommendations | {recommendations['recommendation_count']} (scale={recommendations['action_counts']['scale']}, pause={recommendations['action_counts']['pause']}, retest={recommendations['action_counts']['retest']}) |
| CSV exports | {exports['export_count']} files |

---

## Mart table inventory

Database: `{_safe_database_path(campaign)}`

{chr(10).join(mart_lines)}

---

## A/B test outcomes (Hillstrom)

| Treatment | Recipients | Conversion rate | Absolute lift | Statistically significant |
|-----------|------------|-----------------|---------------|---------------------------|
| control | {control['recipients']:,} | {control['conversion_rate'] * 100:.4f}% | 0.00% | — |
| mens_email | {mens['recipients']:,} | {mens['conversion_rate'] * 100:.4f}% | {mens['absolute_lift'] * 100:.2f}% | {mens['statistically_significant']} |
| womens_email | {womens['recipients']:,} | {womens['conversion_rate'] * 100:.4f}% | {womens['absolute_lift'] * 100:.2f}% | {womens['statistically_significant']} |

Significant treatments: {", ".join(ab_test.get('significant_treatments', []))}

---

## Forecast accuracy

| Model | MAE | RMSE | MAPE |
|-------|-----|------|------|
| {forecast['selected_model']} (selected) | {forecast['selected_metrics']['mae']:,.1f} | {forecast['selected_metrics']['rmse']:,.1f} | {forecast['selected_metrics']['mape']:.1f}% |

Holdout hours: {forecast['holdout_hours']} | Train hours: {forecast['train_hours']}

---

## Export inventory

Excel workbook: `{exports['excel_workbook']}`  
Tableau manifest: `{exports['tableau_manifest']}`

{chr(10).join(export_lines)}

---

## Week 2 pipeline (frozen order)

{pipeline_lines}

Regenerate this lock after any analytics logic change:

```bash
python scripts/generate_week2_analytics_lock.py
```

---

## Validation status

Validation success: **{validation.get('success', False)}**  
Checks passed: **{validation.get('passed_count', 0)} / {validation.get('passed_count', 0) + validation.get('failed_count', 0)}**

{chr(10).join(validation_lines)}

---

## Change policy

1. Do not edit locked statistics manually in stakeholder docs.
2. Re-run the full Week 2 pipeline if mart logic or source data changes.
3. Regenerate this document with `generate_week2_analytics_lock.py`.
4. Re-run `pytest -q` after any pipeline or portfolio doc changes.

---

## Phase 3 boundary

All Phase 3 portfolio deliverables are **complete**:

- Tableau dashboard screenshots (6 PNG pages) — `tableau/screenshots/`, `docs/tableau_dashboard_guide.md`
- Excel workbook screenshots (6 PNG pages) — `excel/screenshots/`, `docs/excel_workbook_guide.md`
- Final README case study — Key Findings section in README
- Final tests + cleanup — `docs/portfolio_completion.md`
- Resume / interview prep — `docs/resume_bullets.md`, `docs/interview_prep.md`, `docs/linkedin_summary.md`

The Tableau `.twbx` and Excel `.xlsx` workbooks are local/gitignored and optional; PNG screenshots are the tracked portfolio artifacts.
"""


def generate_week2_analytics_lock(output_path: Path | None = None) -> Path:
    summaries = validate_required_summaries()

    for key in ("campaign", "funnel", "ab_test", "forecast", "recommendations", "exports"):
        if not summaries[key].get("success"):
            raise RuntimeError(
                f"{key} summary indicates failures. "
                "Run the full Week 2 pipeline successfully before locking."
            )

    if not summaries["validation"].get("success"):
        raise RuntimeError(
            "Validation summary indicates failures. "
            "Run `python scripts/validate_data.py` successfully before locking Week 2."
        )

    content = build_lock_document(summaries)
    target = output_path or WEEK2_ANALYTICS_LOCK_DOC
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def main() -> int:
    print("=" * 60)
    print("Week 2 analytics lock")
    print("=" * 60)

    try:
        output_path = generate_week2_analytics_lock()
        print(f"Wrote {output_path}")
        print("Week 2 marketing analytics are locked.")
        return 0
    except (FileNotFoundError, RuntimeError, KeyError) as exc:
        print(f"Lock generation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
