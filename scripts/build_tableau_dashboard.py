#!/usr/bin/env python3
"""Build Tableau dashboard screenshots and workbook build spec from mart CSV exports."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyBboxPatch

from paths import (
    EXPORTS_DIR,
    MARTS_DIR,
    PROJECT_ROOT,
    TABLEAU_BUILD_SUMMARY,
    TABLEAU_DASHBOARD_SPEC,
    TABLEAU_DASHBOARD_GUIDE,
    TABLEAU_SCREENSHOTS_DIR,
)

REQUIRED_EXPORTS = (
    "campaign_kpis.csv",
    "ctr_trends.csv",
    "segment_performance.csv",
    "ab_test_results.csv",
    "forecast_results.csv",
    "recommendation_matrix.csv",
)

SCREENSHOT_PAGES = (
    ("01_executive_overview.png", "Executive Overview"),
    ("02_ctr_trends.png", "CTR Trends by Hour"),
    ("03_segment_performance.png", "Segment Performance"),
    ("04_ab_test_results.png", "Email A/B Test Results"),
    ("05_forecast.png", "Click Forecast"),
    ("06_recommendations.png", "Recommendations Matrix"),
)

COLORS = {
    "primary": "#1f4e79",
    "accent": "#2e86ab",
    "scale": "#2d6a4f",
    "pause": "#bc4749",
    "retest": "#e9c46a",
    "muted": "#6c757d",
    "bg": "#f8f9fa",
}


def _ensure_exports_exist(exports_dir: Path) -> None:
    missing = [name for name in REQUIRED_EXPORTS if not (exports_dir / name).exists()]
    if missing:
        raise FileNotFoundError(
            "Missing mart export CSV files:\n  - "
            + "\n  - ".join(missing)
            + "\nRun `python scripts/export_dashboard_data.py` first."
        )


def _load_exports(exports_dir: Path) -> dict[str, pd.DataFrame]:
    return {name: pd.read_csv(exports_dir / name) for name in REQUIRED_EXPORTS}


def _style_axes(ax, title: str, subtitle: str = "") -> None:
    ax.set_title(title, fontsize=16, fontweight="bold", color=COLORS["primary"], pad=16)
    if subtitle:
        ax.text(
            0.0,
            1.02,
            subtitle,
            transform=ax.transAxes,
            fontsize=10,
            color=COLORS["muted"],
            va="bottom",
        )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_facecolor("white")


def render_executive_overview(campaign: pd.DataFrame, recommendations: pd.DataFrame, path: Path) -> None:
    row = campaign.iloc[0]
    impressions = int(row["impressions"])
    clicks = int(row["clicks"])
    ctr = float(row["ctr"]) * 100
    scale_count = int((recommendations["action"] == "Scale").sum())
    pause_count = int((recommendations["action"] == "Pause").sum())
    retest_count = int((recommendations["action"] == "Retest").sum())

    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor(COLORS["bg"])
    ax.axis("off")

    ax.text(0.02, 0.95, "Marketing Analytics — Executive Overview", fontsize=20, fontweight="bold", color=COLORS["primary"])
    ax.text(0.02, 0.90, "Avazu mobile display + Hillstrom email experiment", fontsize=11, color=COLORS["muted"])

    cards = [
        ("Impressions", f"{impressions:,}", COLORS["primary"]),
        ("Clicks", f"{clicks:,}", COLORS["accent"]),
        ("Portfolio CTR", f"{ctr:.2f}%", COLORS["scale"]),
        ("Recommendations", f"{len(recommendations)}", COLORS["primary"]),
    ]
    x_positions = [0.05, 0.28, 0.51, 0.74]
    for x, (label, value, color) in zip(x_positions, cards):
        patch = FancyBboxPatch(
            (x, 0.55),
            0.20,
            0.25,
            boxstyle="round,pad=0.02,rounding_size=0.02",
            linewidth=1,
            edgecolor="#dee2e6",
            facecolor="white",
            transform=ax.transAxes,
        )
        ax.add_patch(patch)
        ax.text(x + 0.10, 0.70, value, ha="center", va="center", fontsize=22, fontweight="bold", color=color, transform=ax.transAxes)
        ax.text(x + 0.10, 0.60, label, ha="center", va="center", fontsize=11, color=COLORS["muted"], transform=ax.transAxes)

    ax.text(0.05, 0.42, "Recommendation mix", fontsize=13, fontweight="bold", color=COLORS["primary"], transform=ax.transAxes)
    action_cards = [
        ("Scale", scale_count, COLORS["scale"]),
        ("Pause", pause_count, COLORS["pause"]),
        ("Retest", retest_count, COLORS["retest"]),
    ]
    for idx, (label, count, color) in enumerate(action_cards):
        x = 0.05 + idx * 0.18
        ax.add_patch(
            FancyBboxPatch(
                (x, 0.18),
                0.14,
                0.18,
                boxstyle="round,pad=0.02,rounding_size=0.02",
                linewidth=0,
                facecolor=color,
                alpha=0.15,
                transform=ax.transAxes,
            )
        )
        ax.text(x + 0.07, 0.30, str(count), ha="center", fontsize=18, fontweight="bold", color=color, transform=ax.transAxes)
        ax.text(x + 0.07, 0.22, label, ha="center", fontsize=11, color=COLORS["primary"], transform=ax.transAxes)

    ax.text(0.05, 0.06, "Source: DuckDB marts exported to data/exports/", fontsize=9, color=COLORS["muted"], transform=ax.transAxes)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def render_ctr_trends(trends: pd.DataFrame, path: Path) -> None:
    frame = trends.sort_values("event_hour")
    hours = frame["event_hour"].astype(int)
    ctr_pct = frame["ctr"] * 100

    fig, ax1 = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor(COLORS["bg"])
    _style_axes(ax1, "CTR Trends by Hour", "Hourly engagement on 2014-10-21")

    ax1.bar(hours, frame["impressions"] / 1000, color="#ced4da", alpha=0.7, label="Impressions (thousands)")
    ax1.set_xlabel("Hour of day")
    ax1.set_ylabel("Impressions (thousands)")
    ax1.set_xticks(hours)

    ax2 = ax1.twinx()
    ax2.plot(hours, ctr_pct, color=COLORS["accent"], marker="o", linewidth=2.5, label="CTR %")
    ax2.set_ylabel("CTR (%)")
    ax2.spines["top"].set_visible(False)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def render_segment_performance(segments: pd.DataFrame, path: Path, min_impressions: int = 1000, top_n: int = 10) -> None:
    frame = segments[segments["impressions"] >= min_impressions].copy()
    frame = frame.sort_values(["ctr", "impressions"], ascending=[False, False]).head(top_n)
    frame["segment_label"] = (
        "d" + frame["device_type"].astype(str)
        + " | "
        + frame["app_category"].astype(str).str[:8]
        + " | "
        + frame["site_category"].astype(str).str[:8]
    )
    frame = frame.sort_values("ctr", ascending=True)

    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor(COLORS["bg"])
    _style_axes(ax, "Top Segment CTR", f"Segments with >= {min_impressions:,} impressions")

    colors = [COLORS["scale"] if ctr >= 0.164074 else COLORS["pause"] for ctr in frame["ctr"]]
    ax.barh(frame["segment_label"], frame["ctr"] * 100, color=colors)
    ax.axvline(16.4074, color=COLORS["muted"], linestyle="--", linewidth=1.5, label="Portfolio CTR 16.41%")
    ax.set_xlabel("CTR (%)")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def render_ab_test_results(ab_results: pd.DataFrame, path: Path) -> None:
    frame = ab_results.copy()
    frame["conversion_pct"] = frame["conversion_rate"] * 100
    labels = frame["treatment_label"].tolist()
    colors = [
        COLORS["muted"],
        COLORS["scale"] if frame.iloc[1]["statistically_significant"] else COLORS["accent"],
        COLORS["scale"] if frame.iloc[2]["statistically_significant"] else COLORS["accent"],
    ]

    fig, axes = plt.subplots(1, 2, figsize=(12, 7))
    fig.patch.set_facecolor(COLORS["bg"])

    ax = axes[0]
    _style_axes(ax, "Visit Conversion Rate by Treatment")
    ax.bar(labels, frame["conversion_pct"], color=colors)
    ax.set_ylabel("Conversion rate (%)")
    ax.tick_params(axis="x", rotation=15)

    ax2 = axes[1]
    _style_axes(ax2, "Absolute Lift vs Control")
    lift_frame = frame[frame["treatment_group"] != "control"].copy()
    ax2.bar(
        lift_frame["treatment_label"],
        lift_frame["absolute_lift"] * 100,
        color=[COLORS["scale"], COLORS["scale"]],
    )
    ax2.set_ylabel("Absolute lift (percentage points)")
    ax2.tick_params(axis="x", rotation=15)

    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def render_forecast(forecast: pd.DataFrame, path: Path) -> None:
    row = forecast.iloc[0]
    actual = int(row["actual_clicks"])
    predicted = float(row["forecast_clicks"])
    mape = float(row["mape"])

    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor(COLORS["bg"])
    _style_axes(
        ax,
        "Hourly Click Forecast (Holdout)",
        f"Model: {row['model_name']} | MAPE: {mape:.1f}% — directional only on single-day data",
    )

    ax.bar(["Actual clicks", "Forecast clicks"], [actual, predicted], color=[COLORS["primary"], COLORS["accent"]])
    ax.set_ylabel("Clicks")
    for idx, value in enumerate([actual, predicted]):
        ax.text(idx, value, f"{value:,.0f}", ha="center", va="bottom", fontsize=11)

    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def render_recommendations(recommendations: pd.DataFrame, path: Path) -> None:
    counts = recommendations["action"].value_counts().reindex(["Scale", "Pause", "Retest"], fill_value=0)
    color_map = {"Scale": COLORS["scale"], "Pause": COLORS["pause"], "Retest": COLORS["retest"]}

    fig, axes = plt.subplots(1, 2, figsize=(12, 7))
    fig.patch.set_facecolor(COLORS["bg"])

    ax = axes[0]
    _style_axes(ax, "Recommendations by Action")
    ax.bar(counts.index, counts.values, color=[color_map[label] for label in counts.index])
    ax.set_ylabel("Count")

    ax2 = axes[1]
    ax2.axis("off")
    ax2.text(0.0, 0.95, "Top actions", fontsize=13, fontweight="bold", color=COLORS["primary"])
    y = 0.82
    for _, row in recommendations.head(6).iterrows():
        action = row["action"]
        ax2.text(0.0, y, f"• [{action}] {row['segment'][:55]}", fontsize=9, color=COLORS["primary"])
        y -= 0.11

    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def build_dashboard_spec(exports_dir: Path) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "workbook_name": "marketing_analytics_dashboard.twbx",
        "data_connection": _display_path(exports_dir),
        "connection_type": "text/csv",
        "pages": [
            {
                "screenshot": filename,
                "title": title,
                "primary_data": REQUIRED_EXPORTS[idx],
            }
            for idx, (filename, title) in enumerate(SCREENSHOT_PAGES)
        ],
        "tableau_desktop_steps": [
            "Connect to data/exports/*.csv using Tableau text connector",
            "Create six dashboards matching tableau/screenshots references",
            "Save packaged workbook as tableau/marketing_analytics_dashboard.twbx (local only)",
        ],
    }


def build_tableau_dashboard(
    exports_dir: Path | None = None,
    screenshots_dir: Path | None = None,
    spec_path: Path | None = None,
    summary_path: Path | None = None,
) -> dict[str, Any]:
    exports_dir = exports_dir or EXPORTS_DIR
    screenshots_dir = screenshots_dir or TABLEAU_SCREENSHOTS_DIR
    spec_path = spec_path or TABLEAU_DASHBOARD_SPEC
    summary_path = summary_path or TABLEAU_BUILD_SUMMARY

    _ensure_exports_exist(exports_dir)
    data = _load_exports(exports_dir)
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    outputs = {
        "01_executive_overview.png": lambda p: render_executive_overview(
            data["campaign_kpis.csv"], data["recommendation_matrix.csv"], p
        ),
        "02_ctr_trends.png": lambda p: render_ctr_trends(data["ctr_trends.csv"], p),
        "03_segment_performance.png": lambda p: render_segment_performance(
            data["segment_performance.csv"], p
        ),
        "04_ab_test_results.png": lambda p: render_ab_test_results(data["ab_test_results.csv"], p),
        "05_forecast.png": lambda p: render_forecast(data["forecast_results.csv"], p),
        "06_recommendations.png": lambda p: render_recommendations(
            data["recommendation_matrix.csv"], p
        ),
    }

    written = []
    for filename, renderer in outputs.items():
        target = screenshots_dir / filename
        renderer(target)
        written.append(_display_path(target))

    spec = build_dashboard_spec(exports_dir)
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "exports_dir": _display_path(exports_dir),
        "screenshots_dir": _display_path(screenshots_dir),
        "screenshots": written,
        "screenshot_count": len(written),
        "dashboard_spec": _display_path(spec_path),
        "guide": _display_path(TABLEAU_DASHBOARD_GUIDE),
        "success": True,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    print("=" * 60)
    print("Tableau dashboard build")
    print("=" * 60)

    try:
        summary = build_tableau_dashboard()
        print(f"Wrote {summary['screenshot_count']} screenshots to {summary['screenshots_dir']}")
        print(f"Wrote dashboard spec: {summary['dashboard_spec']}")
        print(f"Wrote build summary: {TABLEAU_BUILD_SUMMARY}")
        print()
        print("Next: open docs/tableau_dashboard_guide.md to build the .twbx in Tableau Desktop.")
        return 0
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"Tableau dashboard build failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
