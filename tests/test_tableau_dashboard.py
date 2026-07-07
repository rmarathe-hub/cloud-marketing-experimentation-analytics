"""Tableau dashboard build script and artifact contract tests."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

import build_tableau_dashboard as tableau_builder
from helpers import (
    TABLEAU_SCREENSHOT_FILES,
    assert_csv_contract,
    read_text,
)
from paths import (
    EXPORTS_DIR,
    PROJECT_ROOT,
    TABLEAU_BUILD_SUMMARY,
    TABLEAU_DASHBOARD_GUIDE,
    TABLEAU_DASHBOARD_SPEC,
    TABLEAU_README,
    TABLEAU_SCREENSHOTS_DIR,
)

pytestmark = [pytest.mark.unit, pytest.mark.exports, pytest.mark.tableau]

EXPECTED_PAGES = (
    ("01_executive_overview.png", "Executive Overview"),
    ("02_ctr_trends.png", "CTR Trends by Hour"),
    ("03_segment_performance.png", "Segment Performance"),
    ("04_ab_test_results.png", "Email A/B Test Results"),
    ("05_forecast.png", "Click Forecast"),
    ("06_recommendations.png", "Recommendations Matrix"),
)


def _copy_exports_to(tmp_exports: Path) -> None:
    tmp_exports.mkdir(parents=True, exist_ok=True)
    for csv_name in tableau_builder.REQUIRED_EXPORTS:
        source = EXPORTS_DIR / csv_name
        if source.is_file():
            shutil.copy2(source, tmp_exports / csv_name)


@pytest.fixture
def tableau_build_bundle(tmp_path):
    exports = tmp_path / "data" / "exports"
    screenshots = tmp_path / "tableau" / "screenshots"
    spec_path = tmp_path / "tableau" / "dashboard_spec.json"
    summary_path = tmp_path / "data" / "processed" / "tableau_build_summary.json"

    _copy_exports_to(exports)
    missing = [name for name in tableau_builder.REQUIRED_EXPORTS if not (exports / name).is_file()]
    if missing:
        pytest.skip(f"Local export CSVs missing: {missing}")

    summary = tableau_builder.build_tableau_dashboard(
        exports_dir=exports,
        screenshots_dir=screenshots,
        spec_path=spec_path,
        summary_path=summary_path,
    )
    return {
        "exports": exports,
        "screenshots": screenshots,
        "spec_path": spec_path,
        "summary_path": summary_path,
        "summary": summary,
    }


def test_tableau_dashboard_guide_exists() -> None:
    assert TABLEAU_DASHBOARD_GUIDE.is_file()
    text = read_text(TABLEAU_DASHBOARD_GUIDE)
    assert "Executive overview" in text
    assert "data/exports/" in text


def test_tableau_readme_exists() -> None:
    assert TABLEAU_README.is_file()
    assert "build_tableau_dashboard.py" in read_text(TABLEAU_README)


def test_tableau_screenshot_constant_matches_builder() -> None:
    assert TABLEAU_SCREENSHOT_FILES == tuple(name for name, _ in tableau_builder.SCREENSHOT_PAGES)


@pytest.mark.parametrize("filename,title", EXPECTED_PAGES)
def test_builder_writes_screenshot(tmp_path, filename: str, title: str) -> None:
    exports = tmp_path / "exports"
    screenshots = tmp_path / "screenshots"
    _copy_exports_to(exports)
    missing = [name for name in tableau_builder.REQUIRED_EXPORTS if not (exports / name).is_file()]
    if missing:
        pytest.skip(f"Local export CSVs missing: {missing}")

    summary = tableau_builder.build_tableau_dashboard(
        exports_dir=exports,
        screenshots_dir=screenshots,
        spec_path=tmp_path / "dashboard_spec.json",
        summary_path=tmp_path / "summary.json",
    )
    screenshot = screenshots / filename
    assert screenshot.is_file(), f"Missing screenshot for {title}"
    assert screenshot.stat().st_size > 5_000
    assert filename in [Path(path).name for path in summary["screenshots"]]


def test_builder_writes_dashboard_spec(tableau_build_bundle) -> None:
    spec = json.loads(tableau_build_bundle["spec_path"].read_text(encoding="utf-8"))
    assert spec["workbook_name"] == "marketing_analytics_dashboard.twbx"
    assert len(spec["pages"]) == 6
    assert spec["pages"][0]["primary_data"] == "campaign_kpis.csv"


def test_builder_writes_summary(tableau_build_bundle) -> None:
    summary = tableau_build_bundle["summary"]
    assert summary["success"] is True
    assert summary["screenshot_count"] == 6
    assert tableau_build_bundle["summary_path"].is_file()


def test_builder_fails_without_exports(tmp_path) -> None:
    empty_exports = tmp_path / "exports"
    empty_exports.mkdir()
    with pytest.raises(FileNotFoundError, match="Missing mart export CSV"):
        tableau_builder.build_tableau_dashboard(
            exports_dir=empty_exports,
            screenshots_dir=tmp_path / "screenshots",
            spec_path=tmp_path / "spec.json",
            summary_path=tmp_path / "summary.json",
        )


def test_production_tableau_screenshots_exist() -> None:
    for name in TABLEAU_SCREENSHOT_FILES:
        path = TABLEAU_SCREENSHOTS_DIR / name
        assert path.is_file(), f"Missing required screenshot: {name}"
        assert path.stat().st_size > 5_000


def test_production_dashboard_spec_exists() -> None:
    if not TABLEAU_DASHBOARD_SPEC.is_file():
        pytest.skip("Run: python scripts/build_tableau_dashboard.py")
    spec = json.loads(TABLEAU_DASHBOARD_SPEC.read_text(encoding="utf-8"))
    assert len(spec["pages"]) == 6


def test_exports_used_by_tableau_builder() -> None:
    for csv_name in tableau_builder.REQUIRED_EXPORTS:
        path = EXPORTS_DIR / csv_name
        if not path.is_file():
            pytest.skip(f"Missing export: {csv_name}")
        assert_csv_contract(path)


def test_readme_links_tableau_guide() -> None:
    readme = read_text(PROJECT_ROOT / "README.md")
    assert "tableau_dashboard_guide.md" in readme
    assert "build_tableau_dashboard.py" in readme
