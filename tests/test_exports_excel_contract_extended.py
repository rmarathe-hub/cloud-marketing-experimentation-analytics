"""Extended exports and Excel workbook contract tests."""

from __future__ import annotations

import json

import pytest
from openpyxl import load_workbook

import export_dashboard_data as dashboard_exports
from helpers import PROJECT_ROOT, EXCEL_WORKBOOK_SHEETS, MART_CSV_EXPORTS, read_text

EXPORT_SCRIPT = PROJECT_ROOT / "scripts" / "export_dashboard_data.py"

pytestmark = [pytest.mark.exports, pytest.mark.excel, pytest.mark.unit]


def test_export_module_defines_six_csv_exports():
    assert len(dashboard_exports.MART_CSV_EXPORTS) == 5
    assert dashboard_exports.RECOMMENDATION_MATRIX_CSV == "recommendation_matrix.csv"


@pytest.mark.parametrize("csv_name", MART_CSV_EXPORTS)
def test_export_csv_name_in_module_mapping(csv_name: str):
    table_names = [item[1] for item in dashboard_exports.MART_CSV_EXPORTS]
    assert csv_name in table_names or csv_name == dashboard_exports.RECOMMENDATION_MATRIX_CSV


@pytest.mark.parametrize("sheet_name", EXCEL_WORKBOOK_SHEETS)
def test_excel_sheet_constant_matches_export_builder(sheet_name: str):
    assert sheet_name in read_text(EXPORT_SCRIPT)


def test_export_script_does_not_create_tableau_workbook():
    text = read_text(EXPORT_SCRIPT).lower()
    assert ".twbx" not in text
    assert "tableau desktop" not in text


def test_export_script_supports_optional_s3_flag():
    text = read_text(EXPORT_SCRIPT)
    assert "--upload-s3" in text
    assert "upload_to_s3" in text


@pytest.mark.parametrize("sheet_name", EXCEL_WORKBOOK_SHEETS)
def test_excel_sheet_names_are_unique(sheet_name: str):
    assert EXCEL_WORKBOOK_SHEETS.count(sheet_name) == 1


def test_tableau_manifest_constant_name():
    assert dashboard_exports.TABLEAU_MANIFEST_JSON == "tableau_data_manifest.json"


def test_export_mart_table_excludes_created_at_column():
    assert "EXCLUDE (created_at)" in read_text(EXPORT_SCRIPT)
