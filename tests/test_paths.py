"""paths.py contract tests."""

from __future__ import annotations

from pathlib import Path

import pytest

import paths

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "attr_name",
    [
        "PROJECT_ROOT",
        "DATA_DIR",
        "RAW_DIR",
        "PROCESSED_DIR",
        "MARTS_DIR",
        "EXPORTS_DIR",
        "DOCS_DIR",
        "AVAZU_RAW_CSV",
        "HILLSTROM_RAW_CSV",
        "RAW_PROFILE_SUMMARY",
        "AVAZU_CLEAN_PARQUET",
        "HILLSTROM_CLEAN_PARQUET",
        "CLEANING_SUMMARY",
    ],
)
def test_paths_module_defines_expected_constant(attr_name: str) -> None:
    value = getattr(paths, attr_name)
    assert isinstance(value, Path)


def test_all_paths_live_inside_project_root() -> None:
    root = paths.PROJECT_ROOT.resolve()
    path_attrs = [
        paths.DATA_DIR,
        paths.RAW_DIR,
        paths.PROCESSED_DIR,
        paths.MARTS_DIR,
        paths.EXPORTS_DIR,
        paths.DOCS_DIR,
        paths.AVAZU_RAW_CSV,
        paths.HILLSTROM_RAW_CSV,
        paths.RAW_PROFILE_SUMMARY,
        paths.AVAZU_CLEAN_PARQUET,
        paths.HILLSTROM_CLEAN_PARQUET,
        paths.CLEANING_SUMMARY,
    ]
    for path in path_attrs:
        resolved = path.resolve()
        assert str(resolved).startswith(str(root))


def test_key_filenames() -> None:
    assert paths.AVAZU_RAW_CSV.name == "avazu_train.csv"
    assert paths.HILLSTROM_RAW_CSV.name == "hillstrom_email.csv"
    assert paths.AVAZU_CLEAN_PARQUET.name == "avazu_clean.parquet"
    assert paths.HILLSTROM_CLEAN_PARQUET.name == "hillstrom_clean.parquet"


def test_directories_can_be_created(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(paths, "RAW_DIR", tmp_path / "raw")
    monkeypatch.setattr(paths, "PROCESSED_DIR", tmp_path / "processed")
    paths.RAW_DIR.mkdir(parents=True, exist_ok=True)
    paths.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    assert paths.RAW_DIR.is_dir()
    assert paths.PROCESSED_DIR.is_dir()
