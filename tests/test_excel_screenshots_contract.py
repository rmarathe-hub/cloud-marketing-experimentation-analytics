"""Excel workbook screenshot portfolio deliverable contract tests."""

from __future__ import annotations

import struct
from pathlib import Path

import pytest

from helpers import (
    EXCEL_SCREENSHOT_FILES,
    README_EXCEL_COMPLETE_PHRASES,
    README_XLSX_FORBIDDEN_PHRASES,
    TABLEAU_EXPORT_CSVS,
    read_text,
)
from paths import EXCEL_SCREENSHOTS_DIR, EXCEL_WORKBOOK_GUIDE, PROJECT_ROOT

pytestmark = [pytest.mark.unit, pytest.mark.docs, pytest.mark.excel]

MIN_PNG_WIDTH = 900
MIN_PNG_HEIGHT = 500
MIN_PNG_BYTES = 5_000


def _png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    assert header[:8] == b"\x89PNG\r\n\x1a\n", f"{path.name} is not a valid PNG"
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def test_excel_screenshots_directory_exists() -> None:
    assert EXCEL_SCREENSHOTS_DIR.is_dir()


@pytest.mark.parametrize("filename", EXCEL_SCREENSHOT_FILES)
def test_required_excel_screenshot_png_exists(filename: str) -> None:
    path = EXCEL_SCREENSHOTS_DIR / filename
    assert path.is_file(), f"Missing required Excel screenshot: {filename}"


@pytest.mark.parametrize("filename", EXCEL_SCREENSHOT_FILES)
def test_required_excel_screenshot_png_is_non_empty(filename: str) -> None:
    path = EXCEL_SCREENSHOTS_DIR / filename
    assert path.stat().st_size >= MIN_PNG_BYTES, f"{filename} is too small"


@pytest.mark.parametrize("filename", EXCEL_SCREENSHOT_FILES)
def test_required_excel_screenshot_png_has_reasonable_dimensions(filename: str) -> None:
    path = EXCEL_SCREENSHOTS_DIR / filename
    width, height = _png_dimensions(path)
    assert width >= MIN_PNG_WIDTH
    assert height >= MIN_PNG_HEIGHT


@pytest.mark.parametrize("filename", EXCEL_SCREENSHOT_FILES)
def test_readme_references_excel_screenshot_path(filename: str) -> None:
    readme = read_text(PROJECT_ROOT / "README.md")
    assert f"excel/screenshots/{filename}" in readme


def test_readme_mentions_excel_workbook_screenshots() -> None:
    readme = read_text(PROJECT_ROOT / "README.md").lower()
    assert "excel" in readme
    assert "workbook screenshots" in readme or "excel workbook screenshots" in readme


def test_readme_states_excel_pngs_are_tracked_portfolio_artifact() -> None:
    readme = read_text(PROJECT_ROOT / "README.md").lower()
    assert "tracked portfolio artifact" in readme
    assert "excel/screenshots" in readme


def test_readme_states_xlsx_is_local_and_not_required() -> None:
    readme = read_text(PROJECT_ROOT / "README.md").lower()
    assert "gitignored" in readme
    assert ".xlsx" in readme or "xlsx" in readme
    assert "not required" in readme


def test_readme_marks_excel_workbook_complete() -> None:
    readme = read_text(PROJECT_ROOT / "README.md")
    for phrase in README_EXCEL_COMPLETE_PHRASES:
        assert phrase in readme


@pytest.mark.parametrize("phrase", README_XLSX_FORBIDDEN_PHRASES)
def test_readme_does_not_claim_xlsx_is_tracked_or_required(phrase: str) -> None:
    readme = read_text(PROJECT_ROOT / "README.md").lower()
    assert phrase.lower() not in readme


def test_excel_workbook_guide_exists() -> None:
    assert EXCEL_WORKBOOK_GUIDE.is_file()


def test_excel_workbook_guide_references_exports_folder() -> None:
    assert "data/exports/" in read_text(EXCEL_WORKBOOK_GUIDE)


def test_excel_workbook_guide_references_screenshot_folder() -> None:
    assert "excel/screenshots/" in read_text(EXCEL_WORKBOOK_GUIDE)


@pytest.mark.parametrize("csv_name", TABLEAU_EXPORT_CSVS)
def test_excel_workbook_guide_references_input_csv(csv_name: str) -> None:
    assert csv_name in read_text(EXCEL_WORKBOOK_GUIDE)


def test_excel_workbook_guide_states_xlsx_is_local_gitignored_optional() -> None:
    guide = read_text(EXCEL_WORKBOOK_GUIDE).lower()
    assert "gitignored" in guide
    assert ".xlsx" in guide or "xlsx" in guide
    assert "optional" in guide


def test_excel_workbook_guide_does_not_require_xlsx_as_tracked_deliverable() -> None:
    guide = read_text(EXCEL_WORKBOOK_GUIDE).lower()
    assert "version-controlled" in guide or "tracked" in guide
    for phrase in ("xlsx is required", ".xlsx is included", "xlsx is committed", "xlsx is tracked"):
        assert phrase not in guide


def test_gitignore_ignores_excel_workbook_files() -> None:
    gitignore = read_text(PROJECT_ROOT / ".gitignore")
    assert "excel/*.xlsx" in gitignore
    assert "excel/*.xlsm" in gitignore


def test_gitignore_does_not_ignore_excel_screenshot_pngs() -> None:
    gitignore = read_text(PROJECT_ROOT / ".gitignore")
    assert "!excel/screenshots/" in gitignore
    assert "excel/screenshots/*.png" not in gitignore


def test_xlsx_workbook_is_not_required_to_exist() -> None:
    workbook = PROJECT_ROOT / "excel" / "marketing_executive_workbook.xlsx"
    assert not workbook.is_file() or workbook.is_file()
