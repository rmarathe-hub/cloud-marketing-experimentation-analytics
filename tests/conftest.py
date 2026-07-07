"""Pytest fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

from helpers import (
    PROJECT_ROOT,
    tiny_avazu_dataframe,
    tiny_hillstrom_dataframe,
    write_tiny_avazu_csv,
    write_tiny_hillstrom_csv,
)

# Ensure scripts directory is importable.
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture
def tiny_avazu_df() -> pd.DataFrame:
    return tiny_avazu_dataframe()


@pytest.fixture
def tiny_hillstrom_df() -> pd.DataFrame:
    return tiny_hillstrom_dataframe()


@pytest.fixture
def temp_data_dirs(tmp_path: Path) -> dict[str, Path]:
    raw_dir = tmp_path / "data" / "raw"
    processed_dir = tmp_path / "data" / "processed"
    raw_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)
    return {
        "root": tmp_path,
        "raw": raw_dir,
        "processed": processed_dir,
        "avazu_raw": write_tiny_avazu_csv(raw_dir / "avazu_train.csv"),
        "hillstrom_raw": write_tiny_hillstrom_csv(raw_dir / "hillstrom_email.csv"),
    }
