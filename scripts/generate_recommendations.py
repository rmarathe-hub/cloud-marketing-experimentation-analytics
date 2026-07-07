#!/usr/bin/env python3
"""Generate recommendations and executive summary docs from analytics marts."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb

from create_duckdb_database import DatabaseConfig, _display_path, load_config
from paths import (
    EXECUTIVE_SUMMARY_DOC,
    RECOMMENDATIONS_DOC,
    RECOMMENDATIONS_SUMMARY,
)

DEFAULT_MIN_IMPRESSIONS = 1_000
CTR_SCALE_MULTIPLIER = 1.15
CTR_PAUSE_MULTIPLIER = 0.75
FORECAST_MAPE_RETEST_THRESHOLD = 100.0


@dataclass(frozen=True)
class Recommendation:
    channel: str
    segment: str
    metric: str
    action: str
    evidence: str
    caveat: str = ""


def ensure_database_ready(config: DatabaseConfig) -> None:
    if not config.database_path.exists():
        raise RuntimeError(
            f"DuckDB database not found at {config.database_path}. "
            "Run the Week 2 analytics scripts before generating recommendations."
        )


def _mart_has_rows(connection: duckdb.DuckDBPyConnection, table_name: str) -> bool:
    count = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    return int(count) > 0


def ensure_marts_populated(connection: duckdb.DuckDBPyConnection) -> None:
    required = (
        "mart_campaign_kpis",
        "mart_ctr_trends",
        "mart_device_app_performance",
        "mart_ab_test_results",
        "mart_forecast_inputs",
        "mart_forecast_results",
    )
    missing = [name for name in required if not _mart_has_rows(connection, name)]
    if missing:
        raise RuntimeError(
            "Analytics marts are not fully populated. Missing or empty tables:\n  - "
            + "\n  - ".join(missing)
        )


def load_analytics_payload(connection: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    overall_ctr, impressions, clicks = connection.execute(
        """
        SELECT
            CASE WHEN SUM(impressions) = 0 THEN 0.0
                 ELSE SUM(clicks)::DOUBLE / SUM(impressions)::DOUBLE END,
            SUM(impressions),
            SUM(clicks)
        FROM mart_campaign_kpis
        """
    ).fetchone()

    hourly_rows = connection.execute(
        """
        SELECT event_hour, impressions, clicks, ctr
        FROM mart_ctr_trends
        ORDER BY event_hour
        """
    ).fetchall()

    top_segments = connection.execute(
        """
        SELECT device_type, app_category, site_category, banner_pos,
               impressions, clicks, ctr, click_share
        FROM mart_device_app_performance
        WHERE impressions >= ?
        ORDER BY ctr DESC, impressions DESC
        LIMIT 5
        """,
        [DEFAULT_MIN_IMPRESSIONS],
    ).fetchall()

    bottom_segments = connection.execute(
        """
        SELECT device_type, app_category, site_category, banner_pos,
               impressions, clicks, ctr, click_share
        FROM mart_device_app_performance
        WHERE impressions >= ?
        ORDER BY ctr ASC, impressions DESC
        LIMIT 5
        """,
        [DEFAULT_MIN_IMPRESSIONS],
    ).fetchall()

    ab_rows = connection.execute(
        """
        SELECT treatment_group, treatment_label, recipients, conversions,
               conversion_rate, absolute_lift, relative_lift_pct,
               incremental_revenue, p_value, statistically_significant
        FROM mart_ab_test_results
        ORDER BY treatment_group
        """
    ).fetchall()

    forecast_metrics = connection.execute(
        """
        SELECT model_name, mae, rmse, mape
        FROM mart_forecast_results
        LIMIT 1
        """
    ).fetchone()

    return {
        "overall_ctr": float(overall_ctr or 0.0),
        "impressions": int(impressions or 0),
        "clicks": int(clicks or 0),
        "hourly_rows": [
            {
                "event_hour": int(row[0]),
                "impressions": int(row[1]),
                "clicks": int(row[2]),
                "ctr": float(row[3]),
            }
            for row in hourly_rows
        ],
        "top_segments": [
            {
                "device_type": int(row[0]),
                "app_category": row[1],
                "site_category": row[2],
                "banner_pos": int(row[3]),
                "impressions": int(row[4]),
                "clicks": int(row[5]),
                "ctr": float(row[6]),
                "click_share": float(row[7]),
            }
            for row in top_segments
        ],
        "bottom_segments": [
            {
                "device_type": int(row[0]),
                "app_category": row[1],
                "site_category": row[2],
                "banner_pos": int(row[3]),
                "impressions": int(row[4]),
                "clicks": int(row[5]),
                "ctr": float(row[6]),
                "click_share": float(row[7]),
            }
            for row in bottom_segments
        ],
        "ab_results": [
            {
                "treatment_group": row[0],
                "treatment_label": row[1],
                "recipients": int(row[2]),
                "conversions": int(row[3]),
                "conversion_rate": float(row[4]),
                "absolute_lift": float(row[5] or 0.0),
                "relative_lift_pct": float(row[6] or 0.0),
                "incremental_revenue": float(row[7] or 0.0),
                "p_value": None if row[8] is None else float(row[8]),
                "statistically_significant": bool(row[9]),
            }
            for row in ab_rows
        ],
        "forecast": None
        if forecast_metrics is None
        else {
            "model_name": forecast_metrics[0],
            "mae": float(forecast_metrics[1]) if forecast_metrics[1] is not None else None,
            "rmse": float(forecast_metrics[2]) if forecast_metrics[2] is not None else None,
            "mape": float(forecast_metrics[3]) if forecast_metrics[3] is not None else None,
        },
    }


def _segment_label(segment: dict[str, Any]) -> str:
    return (
        f"device={segment['device_type']} | app={segment['app_category']} | "
        f"site={segment['site_category']} | banner={segment['banner_pos']}"
    )


def build_recommendations(payload: dict[str, Any]) -> list[Recommendation]:
    recommendations: list[Recommendation] = []
    overall_ctr = payload["overall_ctr"]

    for segment in payload["top_segments"][:3]:
        if segment["ctr"] >= overall_ctr * CTR_SCALE_MULTIPLIER:
            recommendations.append(
                Recommendation(
                    channel="Mobile display (Avazu)",
                    segment=_segment_label(segment),
                    metric="CTR",
                    action="Scale",
                    evidence=(
                        f"{segment['ctr']:.2%} CTR on {segment['impressions']:,} impressions "
                        f"({segment['click_share']:.1%} click share)"
                    ),
                    caveat="Competition subsample; validate on live inventory before budget shifts.",
                )
            )

    for segment in payload["bottom_segments"][:3]:
        if segment["ctr"] <= overall_ctr * CTR_PAUSE_MULTIPLIER:
            recommendations.append(
                Recommendation(
                    channel="Mobile display (Avazu)",
                    segment=_segment_label(segment),
                    metric="CTR",
                    action="Pause",
                    evidence=(
                        f"{segment['ctr']:.2%} CTR on {segment['impressions']:,} impressions "
                        f"vs {overall_ctr:.2%} portfolio CTR"
                    ),
                    caveat="Confirm spend concentration before pausing; segment still has material volume.",
                )
            )

    if payload["hourly_rows"]:
        best_hour = max(payload["hourly_rows"], key=lambda row: row["ctr"])
        worst_hour = min(payload["hourly_rows"], key=lambda row: row["ctr"])
        recommendations.append(
            Recommendation(
                channel="Mobile display (Avazu)",
                segment=f"Hour {best_hour['event_hour']:02d}",
                metric="Hourly CTR",
                action="Scale",
                evidence=(
                    f"{best_hour['ctr']:.2%} CTR with {best_hour['impressions']:,} impressions"
                ),
                caveat="Single-day sample; confirm hour-of-day pattern across more dates.",
            )
        )
        if worst_hour["ctr"] <= overall_ctr * CTR_PAUSE_MULTIPLIER:
            recommendations.append(
                Recommendation(
                    channel="Mobile display (Avazu)",
                    segment=f"Hour {worst_hour['event_hour']:02d}",
                    metric="Hourly CTR",
                    action="Pause",
                    evidence=(
                        f"{worst_hour['ctr']:.2%} CTR with {worst_hour['impressions']:,} impressions"
                    ),
                    caveat="Hour-level pauses should be tested before full daypart shutdown.",
                )
            )

    for result in payload["ab_results"]:
        if result["treatment_group"] == "control":
            continue
        if result["statistically_significant"] and result["absolute_lift"] > 0:
            recommendations.append(
                Recommendation(
                    channel="Email (Hillstrom)",
                    segment=result["treatment_label"],
                    metric="Visit conversion rate",
                    action="Scale",
                    evidence=(
                        f"+{result['absolute_lift']:.2%} absolute lift "
                        f"({result['relative_lift_pct']:.1f}% relative), "
                        f"p={result['p_value']:.4g}, "
                        f"incremental revenue ${result['incremental_revenue']:,.0f}"
                    ),
                )
            )
        elif not result["statistically_significant"]:
            recommendations.append(
                Recommendation(
                    channel="Email (Hillstrom)",
                    segment=result["treatment_label"],
                    metric="Visit conversion rate",
                    action="Retest",
                    evidence=(
                        f"Lift {result['absolute_lift']:.2%} not significant at alpha 0.05 "
                        f"(p={result['p_value']:.4g})"
                    ),
                )
            )
        elif result["absolute_lift"] <= 0:
            recommendations.append(
                Recommendation(
                    channel="Email (Hillstrom)",
                    segment=result["treatment_label"],
                    metric="Visit conversion rate",
                    action="Pause",
                    evidence=f"Negative lift {result['absolute_lift']:.2%} vs control",
                )
            )

    forecast = payload["forecast"]
    if forecast and forecast.get("mape") is not None:
        action = (
            "Retest"
            if forecast["mape"] >= FORECAST_MAPE_RETEST_THRESHOLD
            else "Scale"
        )
        recommendations.append(
            Recommendation(
                channel="Mobile display (Avazu)",
                segment="Hourly click forecast",
                metric="Forecast accuracy (MAPE)",
                action=action,
                evidence=(
                    f"Model {forecast['model_name']}: MAE={forecast['mae']:,.1f}, "
                    f"RMSE={forecast['rmse']:,.1f}, MAPE={forecast['mape']:.1f}%"
                ),
                caveat="Single-day holdout only; use forecasts for directional planning.",
            )
        )

    return recommendations


def _format_recommendation_table(recommendations: list[Recommendation]) -> str:
    lines = [
        "| Channel | Segment | Metric | Action | Evidence | Caveat |",
        "|---------|---------|--------|--------|----------|--------|",
    ]
    for item in recommendations:
        lines.append(
            f"| {item.channel} | {item.segment} | {item.metric} | "
            f"**{item.action}** | {item.evidence} | {item.caveat} |"
        )
    return "\n".join(lines)


def build_recommendations_markdown(
    payload: dict[str, Any],
    recommendations: list[Recommendation],
) -> str:
    scale_count = sum(1 for item in recommendations if item.action == "Scale")
    pause_count = sum(1 for item in recommendations if item.action == "Pause")
    retest_count = sum(1 for item in recommendations if item.action == "Retest")

    return f"""# Marketing Recommendations

Evidence-based **scale / pause / retest** actions from populated Week 2 analytics marts.

**Generated:** {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}

---

## Summary

| Action | Count |
|--------|------:|
| Scale | {scale_count} |
| Pause | {pause_count} |
| Retest | {retest_count} |

Portfolio CTR: **{payload['overall_ctr']:.4%}** on **{payload['impressions']:,}** impressions
and **{payload['clicks']:,}** clicks.

---

## Recommendation matrix

{_format_recommendation_table(recommendations)}

---

## Decision rules used

| Action | Rule |
|--------|------|
| **Scale** | Segment CTR ≥ {CTR_SCALE_MULTIPLIER:.0%} of portfolio CTR with ≥ {DEFAULT_MIN_IMPRESSIONS:,} impressions, or significant positive email lift |
| **Pause** | Segment CTR ≤ {CTR_PAUSE_MULTIPLIER:.0%} of portfolio CTR with sufficient volume, or negative email lift |
| **Retest** | Non-significant email treatments or forecast MAPE ≥ {FORECAST_MAPE_RETEST_THRESHOLD:.0f}% |

See [business_problem.md](business_problem.md) and [metric_definitions.md](metric_definitions.md).

---

## Regenerate

```bash
python scripts/generate_recommendations.py
```

Requires all six mart tables populated and `data/processed/marketing_analytics.duckdb` available locally.
"""


def build_executive_summary_markdown(
    payload: dict[str, Any],
    recommendations: list[Recommendation],
) -> str:
    top_segment = payload["top_segments"][0] if payload["top_segments"] else None
    best_treatment = max(
        (
            row
            for row in payload["ab_results"]
            if row["treatment_group"] != "control"
        ),
        key=lambda row: row["absolute_lift"],
        default=None,
    )
    forecast = payload["forecast"] or {}

    top_segment_line = (
        f"Top mobile segment CTR **{top_segment['ctr']:.2%}** on "
        f"**{top_segment['impressions']:,}** impressions "
        f"({top_segment['app_category']} / {top_segment['site_category']})."
        if top_segment
        else "Top mobile segment data unavailable."
    )
    treatment_line = (
        f"Strongest email treatment: **{best_treatment['treatment_label']}** with "
        f"**+{best_treatment['absolute_lift']:.2%}** absolute visit lift "
        f"(p={best_treatment['p_value']:.4g})."
        if best_treatment
        else "Email treatment comparison unavailable."
    )
    forecast_line = (
        f"Hourly click forecast MAPE **{forecast['mape']:.1f}%** "
        f"({forecast.get('model_name', 'n/a')}); treat as directional only on single-day data."
        if forecast.get("mape") is not None
        else "Forecast metrics unavailable."
    )

    scale_items = [item for item in recommendations if item.action == "Scale"][:3]
    pause_items = [item for item in recommendations if item.action == "Pause"][:2]

    scale_bullets = "\n".join(
        f"- **Scale:** {item.segment} — {item.evidence}" for item in scale_items
    ) or "- **Scale:** No scale actions met volume and performance thresholds."

    pause_bullets = "\n".join(
        f"- **Pause:** {item.segment} — {item.evidence}" for item in pause_items
    ) or "- **Pause:** No pause actions met volume and underperformance thresholds."

    return f"""# Executive Summary

One-page stakeholder view of Week 2 marketing analytics findings.

**Generated:** {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}

---

## Headline metrics

1. **Mobile CTR:** {payload['overall_ctr']:.4%} across {payload['impressions']:,} impressions ({payload['clicks']:,} clicks).
2. **Segment leader:** {top_segment_line}
3. **Email experiment:** {treatment_line}
4. **Forecast check:** {forecast_line}
5. **Validation:** Recommendations derived from populated DuckDB marts (`mart_campaign_kpis`, `mart_device_app_performance`, `mart_ab_test_results`, `mart_forecast_results`).

---

## Recommended actions

{scale_bullets}
{pause_bullets}

---

## Caveats

- Avazu is a single-day competition subsample; CTR is not a live campaign benchmark.
- Hillstrom `converted` equals `visit`; revenue uses cleaned `spend`.
- Tableau and Excel portfolio deliverables are complete (screenshot PNGs in `tableau/screenshots/` and `excel/screenshots/`).

Full matrix: [recommendations.md](recommendations.md)
"""


def build_summary_json(
    config: DatabaseConfig,
    payload: dict[str, Any],
    recommendations: list[Recommendation],
) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database_path": _display_path(config.database_path),
        "overall_ctr": round(payload["overall_ctr"], 6),
        "impressions": payload["impressions"],
        "clicks": payload["clicks"],
        "recommendation_count": len(recommendations),
        "action_counts": {
            "scale": sum(1 for item in recommendations if item.action == "Scale"),
            "pause": sum(1 for item in recommendations if item.action == "Pause"),
            "retest": sum(1 for item in recommendations if item.action == "Retest"),
        },
        "recommendations": [
            {
                "channel": item.channel,
                "segment": item.segment,
                "metric": item.metric,
                "action": item.action,
                "evidence": item.evidence,
                "caveat": item.caveat,
            }
            for item in recommendations
        ],
        "success": len(recommendations) > 0,
    }


def write_outputs(
    recommendations_doc: str,
    executive_doc: str,
    summary: dict[str, Any],
    recommendations_path: Path | None = None,
    executive_path: Path | None = None,
    summary_path: Path | None = None,
) -> dict[str, Path]:
    rec_path = recommendations_path or RECOMMENDATIONS_DOC
    exec_path = executive_path or EXECUTIVE_SUMMARY_DOC
    sum_path = summary_path or RECOMMENDATIONS_SUMMARY

    rec_path.parent.mkdir(parents=True, exist_ok=True)
    exec_path.parent.mkdir(parents=True, exist_ok=True)
    sum_path.parent.mkdir(parents=True, exist_ok=True)

    rec_path.write_text(recommendations_doc, encoding="utf-8")
    exec_path.write_text(executive_doc, encoding="utf-8")
    sum_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return {
        "recommendations": rec_path,
        "executive_summary": exec_path,
        "summary": sum_path,
    }


def generate_recommendations(
    config: DatabaseConfig | None = None,
    recommendations_path: Path | None = None,
    executive_path: Path | None = None,
    summary_path: Path | None = None,
) -> dict[str, Any]:
    config = config or load_config()
    ensure_database_ready(config)

    connection = duckdb.connect(str(config.database_path), read_only=True)
    try:
        ensure_marts_populated(connection)
        payload = load_analytics_payload(connection)
    finally:
        connection.close()

    recommendations = build_recommendations(payload)
    recommendations_doc = build_recommendations_markdown(payload, recommendations)
    executive_doc = build_executive_summary_markdown(payload, recommendations)
    summary = build_summary_json(config, payload, recommendations)
    paths = write_outputs(
        recommendations_doc,
        executive_doc,
        summary,
        recommendations_path=recommendations_path,
        executive_path=executive_path,
        summary_path=summary_path,
    )

    return {
        "paths": {key: str(path) for key, path in paths.items()},
        "recommendation_count": len(recommendations),
        "action_counts": summary["action_counts"],
        "success": summary["success"],
    }


def main() -> int:
    print("=" * 60)
    print("Recommendations + executive summary")
    print("=" * 60)

    try:
        result = generate_recommendations()
        print(f"Wrote {RECOMMENDATIONS_DOC}")
        print(f"Wrote {EXECUTIVE_SUMMARY_DOC}")
        print(f"Wrote {RECOMMENDATIONS_SUMMARY}")
        print()
        print(
            f"Recommendations: {result['recommendation_count']} "
            f"(scale={result['action_counts']['scale']}, "
            f"pause={result['action_counts']['pause']}, "
            f"retest={result['action_counts']['retest']})"
        )
        if not result["success"]:
            print("No recommendations were generated.", file=sys.stderr)
            return 1
        return 0
    except RuntimeError as exc:
        print(f"Recommendation generation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
