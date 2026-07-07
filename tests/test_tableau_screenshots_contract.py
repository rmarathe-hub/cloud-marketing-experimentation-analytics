"""Tableau screenshot portfolio deliverable contract tests."""

from __future__ import annotations

import struct
from pathlib import Path

import pytest

from helpers import (
    README_CASE_STUDY_COMPLETE_PHRASES,
    README_TWBX_FORBIDDEN_PHRASES,
    TABLEAU_EXPORT_CSVS,
    TABLEAU_SCREENSHOT_FILES,
    read_text,
)
from paths import PROJECT_ROOT, TABLEAU_DASHBOARD_GUIDE, TABLEAU_SCREENSHOTS_DIR

pytestmark = [pytest.mark.unit, pytest.mark.docs, pytest.mark.tableau]

MIN_PNG_WIDTH = 900
MIN_PNG_HEIGHT = 500
MIN_PNG_BYTES = 5_000


def _png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    assert header[:8] == b"\x89PNG\r\n\x1a\n", f"{path.name} is not a valid PNG"
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def test_tableau_screenshots_directory_exists() -> None:
    assert TABLEAU_SCREENSHOTS_DIR.is_dir()


@pytest.mark.parametrize("filename", TABLEAU_SCREENSHOT_FILES)
def test_required_screenshot_png_exists(filename: str) -> None:
    path = TABLEAU_SCREENSHOTS_DIR / filename
    assert path.is_file(), f"Missing required screenshot: {filename}"


@pytest.mark.parametrize("filename", TABLEAU_SCREENSHOT_FILES)
def test_required_screenshot_png_is_non_empty(filename: str) -> None:
    path = TABLEAU_SCREENSHOTS_DIR / filename
    assert path.stat().st_size >= MIN_PNG_BYTES, f"{filename} is too small to be a real screenshot"


@pytest.mark.parametrize("filename", TABLEAU_SCREENSHOT_FILES)
def test_required_screenshot_png_has_reasonable_dimensions(filename: str) -> None:
    path = TABLEAU_SCREENSHOTS_DIR / filename
    width, height = _png_dimensions(path)
    assert width >= MIN_PNG_WIDTH, f"{filename} width {width} < {MIN_PNG_WIDTH}"
    assert height >= MIN_PNG_HEIGHT, f"{filename} height {height} < {MIN_PNG_HEIGHT}"


@pytest.mark.parametrize("filename", TABLEAU_SCREENSHOT_FILES)
def test_readme_references_screenshot_path(filename: str) -> None:
    readme = read_text(PROJECT_ROOT / "README.md")
    assert f"tableau/screenshots/{filename}" in readme


def test_readme_mentions_tableau_dashboard_screenshots() -> None:
    readme = read_text(PROJECT_ROOT / "README.md").lower()
    assert "tableau" in readme
    assert "screenshot" in readme
    assert "dashboard screenshots" in readme


def test_readme_states_pngs_are_tracked_portfolio_artifact() -> None:
    readme = read_text(PROJECT_ROOT / "README.md").lower()
    assert "tracked portfolio artifact" in readme
    assert "png screenshot" in readme or "png screenshots" in readme or "screenshot set" in readme


def test_readme_states_twbx_is_local_and_not_required() -> None:
    readme = read_text(PROJECT_ROOT / "README.md").lower()
    assert "gitignored" in readme
    assert ".twbx" in readme
    assert "not required" in readme


def test_readme_includes_forecast_caveat() -> None:
    readme = read_text(PROJECT_ROOT / "README.md").lower()
    assert "mape" in readme
    assert "single-day" in readme or "single day" in readme
    assert "directional" in readme


def test_readme_includes_case_study_section() -> None:
    readme = read_text(PROJECT_ROOT / "README.md")
    assert "## Key Findings (Case Study)" in readme
    for phrase in README_CASE_STUDY_COMPLETE_PHRASES:
        assert phrase in readme


@pytest.mark.parametrize("phrase", README_TWBX_FORBIDDEN_PHRASES)
def test_readme_does_not_claim_twbx_is_tracked_or_required(phrase: str) -> None:
    readme = read_text(PROJECT_ROOT / "README.md").lower()
    assert phrase.lower() not in readme


def test_tableau_dashboard_guide_exists() -> None:
    assert TABLEAU_DASHBOARD_GUIDE.is_file()


def test_tableau_dashboard_guide_references_exports_folder() -> None:
    guide = read_text(TABLEAU_DASHBOARD_GUIDE)
    assert "data/exports/" in guide


def test_tableau_dashboard_guide_references_screenshot_folder() -> None:
    guide = read_text(TABLEAU_DASHBOARD_GUIDE)
    assert "tableau/screenshots/" in guide


@pytest.mark.parametrize("csv_name", TABLEAU_EXPORT_CSVS)
def test_tableau_dashboard_guide_references_input_csv(csv_name: str) -> None:
    assert csv_name in read_text(TABLEAU_DASHBOARD_GUIDE)


def test_tableau_dashboard_guide_states_twbx_is_local_gitignored_optional() -> None:
    guide = read_text(TABLEAU_DASHBOARD_GUIDE).lower()
    assert "gitignored" in guide
    assert ".twbx" in guide
    assert "optional" in guide


def test_tableau_dashboard_guide_does_not_require_twbx_as_tracked_deliverable() -> None:
    guide = read_text(TABLEAU_DASHBOARD_GUIDE).lower()
    assert "version-controlled artifact" in guide or "tracked" in guide
    assert "not required" in guide or "optional" in guide
    for phrase in ("twbx is required", ".twbx is included", "twbx is committed", "twbx is tracked"):
        assert phrase not in guide


def test_tableau_dashboard_guide_includes_forecast_mape_caveat() -> None:
    guide = read_text(TABLEAU_DASHBOARD_GUIDE).lower()
    assert "314.4%" in guide or "mape 314" in guide
    assert "single-day" in guide or "single day" in guide
    assert "directional" in guide


def test_gitignore_ignores_tableau_workbook_extensions() -> None:
    gitignore = read_text(PROJECT_ROOT / ".gitignore")
    assert "*.twbx" in gitignore
    assert "*.twb" in gitignore
    assert "tableau/*.twbx" in gitignore
    assert "tableau/*.twb" in gitignore


def test_gitignore_does_not_ignore_tableau_screenshot_pngs() -> None:
    gitignore = read_text(PROJECT_ROOT / ".gitignore")
    assert "!tableau/screenshots/" in gitignore
    assert "tableau/screenshots/*.png" not in gitignore


def test_twbx_workbook_is_not_required_to_exist() -> None:
    twbx = PROJECT_ROOT / "tableau" / "marketing_analytics_dashboard.twbx"
    # Absence is valid; this test never opens or parses the file.
    assert not twbx.is_file() or twbx.is_file()
