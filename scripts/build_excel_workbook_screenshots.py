#!/usr/bin/env python3
"""Build Excel workbook portfolio screenshots from mart CSV exports."""

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
    EXCEL_BUILD_SUMMARY,
    EXCEL_SCREENSHOTS_DIR,
    EXCEL_WORKBOOK_GUIDE,
    EXCEL_WORKBOOK_SPEC,
    EXPORTS_DIR,
    PROJECT_ROOT,
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
    ("01_executive_summary.png", "Executive Summary"),
    ("02_campaign_kpis.png", "Campaign KPIs"),
    ("03_ab_test_results.png", "A/B Test Results"),
    ("04_recommendations.png", "Recommendations Matrix"),
    ("05_pivot_recommendations.png", "Pivot Recommendations"),
    ("06_ab_calculator.png", "A/B Calculator"),
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


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


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


def render_executive_summary(campaign: pd.DataFrame, recommendations: pd.DataFrame, path: Path) -> None:
    row = campaign.iloc[0]
    counts = recommendations["action"].value_counts()

    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor(COLORS["bg"])
    ax.axis("off")
    ax.text(0.02, 0.95, "Marketing Executive Workbook — Summary", fontsize=20, fontweight="bold", color=COLORS["primary"])
    ax.text(0.02, 0.90, "Stakeholder view from DuckDB mart exports", fontsize=11, color=COLORS["muted"])

    cards = [
        ("Impressions", f"{int(row['impressions']):,}", COLORS["primary"]),
        ("Clicks", f"{int(row['clicks']):,}", COLORS["accent"]),
        ("Portfolio CTR", f"{float(row['ctr']) * 100:.2f}%", COLORS["scale"]),
        ("Recommendations", str(len(recommendations)), COLORS["primary"]),
    ]
    for idx, (label, value, color) in enumerate(cards):
        x = 0.05 + idx * 0.23
        ax.add_patch(
            FancyBboxPatch(
                (x, 0.55),
                0.20,
                0.25,
                boxstyle="round,pad=0.02,rounding_size=0.02",
                linewidth=1,
                edgecolor="#dee2e6",
                facecolor="white",
                transform=ax.transAxes,
            )
        )
        ax.text(x + 0.10, 0.70, value, ha="center", va="center", fontsize=20, fontweight="bold", color=color, transform=ax.transAxes)
        ax.text(x + 0.10, 0.60, label, ha="center", va="center", fontsize=11, color=COLORS["muted"], transform=ax.transAxes)

    ax.text(0.05, 0.42, "Recommendation actions", fontsize=13, fontweight="bold", color=COLORS["primary"], transform=ax.transAxes)
    for idx, action in enumerate(["Scale", "Pause", "Retest"]):
        color = {"Scale": COLORS["scale"], "Pause": COLORS["pause"], "Retest": COLORS["retest"]}[action]
        x = 0.05 + idx * 0.18
        ax.text(x + 0.07, 0.30, str(int(counts.get(action, 0))), ha="center", fontsize=18, fontweight="bold", color=color, transform=ax.transAxes)
        ax.text(x + 0.07, 0.22, action, ha="center", fontsize=11, color=COLORS["primary"], transform=ax.transAxes)

    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def render_campaign_kpis(campaign: pd.DataFrame, path: Path) -> None:
    row = campaign.iloc[0]
    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor(COLORS["bg"])
    _style_axes(ax, "Campaign KPIs", "Avazu portfolio metrics")
    ax.bar(
        ["Impressions", "Clicks", "CTR (%)"],
        [int(row["impressions"]), int(row["clicks"]), float(row["ctr"]) * 100],
        color=[COLORS["primary"], COLORS["accent"], COLORS["scale"]],
    )
    ax.set_ylabel("Value")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def render_ab_test_results(ab_results: pd.DataFrame, path: Path) -> None:
    frame = ab_results.copy()
    frame["conversion_pct"] = frame["conversion_rate"] * 100
    fig, axes = plt.subplots(1, 2, figsize=(12, 7))
    fig.patch.set_facecolor(COLORS["bg"])
    axes[0].bar(frame["treatment_label"], frame["conversion_pct"], color=[COLORS["muted"], COLORS["scale"], COLORS["scale"]])
    _style_axes(axes[0], "Visit Conversion Rate")
    axes[0].set_ylabel("Conversion rate (%)")
    axes[0].tick_params(axis="x", rotation=15)
    lift = frame[frame["treatment_group"] != "control"]
    axes[1].bar(lift["treatment_label"], lift["absolute_lift"] * 100, color=[COLORS["scale"], COLORS["scale"]])
    _style_axes(axes[1], "Absolute Lift vs Control")
    axes[1].set_ylabel("Absolute lift (pp)")
    axes[1].tick_params(axis="x", rotation=15)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def render_recommendations(recommendations: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor(COLORS["bg"])
    ax.axis("off")
    ax.text(0.0, 0.95, "Recommendations Matrix", fontsize=16, fontweight="bold", color=COLORS["primary"])
    y = 0.85
    for _, row in recommendations.iterrows():
        ax.text(0.0, y, f"[{row['action']}] {row['segment'][:70]}", fontsize=9, color=COLORS["primary"])
        y -= 0.08
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def render_pivot_recommendations(recommendations: pd.DataFrame, path: Path) -> None:
    counts = recommendations["action"].value_counts().reindex(["Scale", "Pause", "Retest"], fill_value=0)
    color_map = {"Scale": COLORS["scale"], "Pause": COLORS["pause"], "Retest": COLORS["retest"]}
    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor(COLORS["bg"])
    _style_axes(ax, "Pivot — Recommendations by Action", "Excel Pivot_Recommendations sheet")
    ax.bar(counts.index, counts.values, color=[color_map[label] for label in counts.index])
    ax.set_ylabel("Count")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def render_ab_calculator(ab_results: pd.DataFrame, path: Path) -> None:
    frame = ab_results.set_index("treatment_label")
    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor(COLORS["bg"])
    ax.axis("off")
    ax.text(0.02, 0.95, "A/B Scenario Calculator", fontsize=18, fontweight="bold", color=COLORS["primary"])
    ax.text(0.02, 0.88, "Editable conversion-rate scenarios for stakeholder what-if analysis", fontsize=10, color=COLORS["muted"])

    labels = ["Conversion rate", "Absolute lift", "Incremental revenue"]
    y = 0.72
    for label in labels:
        ax.text(0.05, y, label, fontsize=11, fontweight="bold", color=COLORS["primary"])
        y -= 0.12

    control = frame.loc["Control (No E-Mail)"]
    mens = frame.loc["Mens E-Mail"]
    womens = frame.loc["Womens E-Mail"]
    ax.text(
        0.45,
        0.78,
        f"Control: {control['conversion_rate'] * 100:.2f}% | "
        f"Mens: {mens['conversion_rate'] * 100:.2f}% | "
        f"Womens: {womens['conversion_rate'] * 100:.2f}%",
        fontsize=10,
        color=COLORS["muted"],
    )
    ax.text(
        0.45,
        0.66,
        f"Mens lift {mens['absolute_lift'] * 100:.2f} pp | Womens lift {womens['absolute_lift'] * 100:.2f} pp",
        fontsize=10,
        color=COLORS["scale"],
    )
    ax.text(
        0.45,
        0.54,
        f"Incremental revenue: Mens ${mens['incremental_revenue']:,.0f} | Womens ${womens['incremental_revenue']:,.0f}",
        fontsize=10,
        color=COLORS["accent"],
    )
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def build_workbook_spec(exports_dir: Path) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "workbook_name": "marketing_executive_workbook.xlsx",
        "data_connection": _display_path(exports_dir),
        "screenshots_dir": _display_path(EXCEL_SCREENSHOTS_DIR),
        "pages": [
            {"screenshot": filename, "title": title, "primary_data": REQUIRED_EXPORTS[min(idx, len(REQUIRED_EXPORTS) - 1)]}
            for idx, (filename, title) in enumerate(SCREENSHOT_PAGES)
        ],
        "notes": [
            "PNG screenshots are the tracked portfolio artifact.",
            "The .xlsx workbook is local/gitignored and optional.",
        ],
    }


def build_excel_workbook_screenshots(
    exports_dir: Path | None = None,
    screenshots_dir: Path | None = None,
    spec_path: Path | None = None,
    summary_path: Path | None = None,
) -> dict[str, Any]:
    exports_dir = exports_dir or EXPORTS_DIR
    screenshots_dir = screenshots_dir or EXCEL_SCREENSHOTS_DIR
    spec_path = spec_path or EXCEL_WORKBOOK_SPEC
    summary_path = summary_path or EXCEL_BUILD_SUMMARY

    _ensure_exports_exist(exports_dir)
    data = _load_exports(exports_dir)
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    outputs = {
        "01_executive_summary.png": lambda p: render_executive_summary(
            data["campaign_kpis.csv"], data["recommendation_matrix.csv"], p
        ),
        "02_campaign_kpis.png": lambda p: render_campaign_kpis(data["campaign_kpis.csv"], p),
        "03_ab_test_results.png": lambda p: render_ab_test_results(data["ab_test_results.csv"], p),
        "04_recommendations.png": lambda p: render_recommendations(data["recommendation_matrix.csv"], p),
        "05_pivot_recommendations.png": lambda p: render_pivot_recommendations(
            data["recommendation_matrix.csv"], p
        ),
        "06_ab_calculator.png": lambda p: render_ab_calculator(data["ab_test_results.csv"], p),
    }

    written = []
    for filename, renderer in outputs.items():
        target = screenshots_dir / filename
        renderer(target)
        written.append(_display_path(target))

    spec = build_workbook_spec(exports_dir)
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "exports_dir": _display_path(exports_dir),
        "screenshots_dir": _display_path(screenshots_dir),
        "screenshots": written,
        "screenshot_count": len(written),
        "workbook_spec": _display_path(spec_path),
        "guide": _display_path(EXCEL_WORKBOOK_GUIDE),
        "success": True,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    print("=" * 60)
    print("Excel workbook screenshot build")
    print("=" * 60)
    try:
        summary = build_excel_workbook_screenshots()
        print(f"Wrote {summary['screenshot_count']} screenshots to {summary['screenshots_dir']}")
        print(f"Wrote workbook spec: {summary['workbook_spec']}")
        print(f"Wrote build summary: {EXCEL_BUILD_SUMMARY}")
        print()
        print("Next: open docs/excel_workbook_guide.md for workbook details.")
        return 0
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"Excel screenshot build failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
