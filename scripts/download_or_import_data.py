#!/usr/bin/env python3
"""Download or import Avazu and Hillstrom raw datasets."""

from __future__ import annotations

import gzip
import os
import shutil
import sys
import tempfile
import urllib.request
from pathlib import Path

import pandas as pd

from paths import (
    AVAZU_COLUMNS,
    AVAZU_RAW_CSV,
    HILLSTROM_RAW_CSV,
    PROCESSED_DIR,
    RAW_DIR,
)

HILLSTROM_URL = (
    "http://www.minethatdata.com/"
    "Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv"
)

# Real Avazu subsample (1M rows) mirrored from the Kaggle competition data.
AVAZU_DROPBOX_1M_URL = (
    "https://www.dropbox.com/s/84jqkc29vfchak8/train_1000000_lines?dl=1"
)

DEFAULT_AVAZU_SAMPLE_ROWS = int(os.getenv("AVAZU_SAMPLE_ROWS", "500000"))


def ensure_directories() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def download_file(url: str, destination: Path, description: str) -> None:
    print(f"Downloading {description}...")
    print(f"  Source: {url}")
    print(f"  Target: {destination}")

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        urllib.request.urlretrieve(url, tmp_path)
        shutil.move(str(tmp_path), destination)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    size_mb = destination.stat().st_size / (1024 * 1024)
    print(f"  Saved ({size_mb:.1f} MB)")


def import_hillstrom_from_path(source: Path, destination: Path | None = None) -> Path:
    """Copy a local Hillstrom CSV into the raw data directory."""
    dest = destination or HILLSTROM_RAW_CSV
    if not source.exists():
        raise FileNotFoundError(f"Hillstrom source file not found: {source}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    return dest


def import_avazu_from_path(
    source: Path,
    destination: Path | None = None,
    sample_rows: int | None = None,
) -> Path:
    """Copy or sample a local Avazu CSV into the raw data directory."""
    dest = destination or AVAZU_RAW_CSV
    if not source.exists():
        raise FileNotFoundError(f"Avazu source file not found: {source}")

    if source.suffix == ".gz":
        return _sample_avazu_from_gzip(source, dest, sample_rows or DEFAULT_AVAZU_SAMPLE_ROWS)

    dest.parent.mkdir(parents=True, exist_ok=True)
    if sample_rows is None:
        shutil.copy2(source, dest)
        return dest

    df = pd.read_csv(source, nrows=sample_rows)
    _write_avazu_csv_from_dataframe(df, dest)
    return dest


def download_hillstrom(force: bool = False) -> Path:
    if HILLSTROM_RAW_CSV.exists() and not force:
        print(f"Hillstrom data already exists: {HILLSTROM_RAW_CSV}")
        return HILLSTROM_RAW_CSV

    download_file(HILLSTROM_URL, HILLSTROM_RAW_CSV, "Hillstrom email experiment data")
    return HILLSTROM_RAW_CSV


def _write_avazu_csv_from_dataframe(df: pd.DataFrame, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(destination, index=False)
    print(f"  Wrote {len(df):,} Avazu rows to {destination}")


def _sample_avazu_from_gzip(
    gzip_path: Path, destination: Path, sample_rows: int
) -> Path:
    print(f"Extracting {sample_rows:,} rows from {gzip_path}...")
    rows: list[list[str]] = []
    with gzip.open(gzip_path, "rt") as handle:
        first_line = handle.readline().strip().split(",")
        if first_line[0] == "id":
            columns = first_line
            collected = 0
        else:
            columns = AVAZU_COLUMNS
            rows.append(first_line)
            collected = 1

        for line in handle:
            if collected >= sample_rows:
                break
            rows.append(line.strip().split(","))
            collected += 1

    df = pd.DataFrame(rows, columns=columns)
    _write_avazu_csv_from_dataframe(df, destination)
    return destination


def _import_avazu_from_kaggle(sample_rows: int) -> Path | None:
    username = os.getenv("KAGGLE_USERNAME")
    key = os.getenv("KAGGLE_KEY")
    if not username or not key:
        return None

    try:
        import kagglehub
    except ImportError:
        print("kagglehub not installed; skipping Kaggle download.")
        return None

    print("Attempting Avazu download via Kaggle API...")
    archive_path = Path(
        kagglehub.competition_download("avazu-ctr-prediction", path="train.gz")
    )

    if archive_path.suffix == ".gz":
        return _sample_avazu_from_gzip(archive_path, AVAZU_RAW_CSV, sample_rows)

    return None


def _import_avazu_from_dropbox(sample_rows: int) -> Path:
    print(f"Streaming {sample_rows:,} Avazu rows from public subsample...")
    print(f"  Source: {AVAZU_DROPBOX_1M_URL}")

    rows: list[list[str]] = []
    with urllib.request.urlopen(AVAZU_DROPBOX_1M_URL) as response:
        for line in response:
            if len(rows) >= sample_rows:
                break
            parts = line.decode("utf-8").strip().split(",")
            if parts and parts[0] == "id":
                continue
            rows.append(parts)

    df = pd.DataFrame(rows, columns=AVAZU_COLUMNS)
    _write_avazu_csv_from_dataframe(df, AVAZU_RAW_CSV)
    return AVAZU_RAW_CSV


def download_avazu(force: bool = False, sample_rows: int | None = None) -> Path:
    sample_rows = sample_rows or DEFAULT_AVAZU_SAMPLE_ROWS

    if AVAZU_RAW_CSV.exists() and not force:
        print(f"Avazu data already exists: {AVAZU_RAW_CSV}")
        return AVAZU_RAW_CSV

    local_gzip = RAW_DIR / "train.gz"
    if local_gzip.exists():
        return _sample_avazu_from_gzip(local_gzip, AVAZU_RAW_CSV, sample_rows)

    source_path = os.getenv("AVAZU_SOURCE_PATH")
    if source_path:
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"AVAZU_SOURCE_PATH not found: {source}")

        if source.suffix == ".gz":
            return _sample_avazu_from_gzip(source, AVAZU_RAW_CSV, sample_rows)

        shutil.copy2(source, AVAZU_RAW_CSV)
        df = pd.read_csv(AVAZU_RAW_CSV, nrows=sample_rows)
        _write_avazu_csv_from_dataframe(df, AVAZU_RAW_CSV)
        return AVAZU_RAW_CSV

    kaggle_result = _import_avazu_from_kaggle(sample_rows)
    if kaggle_result is not None:
        return kaggle_result

    return _import_avazu_from_dropbox(sample_rows)


def main() -> int:
    force = "--force" in sys.argv
    ensure_directories()

    print("=" * 60)
    print("Dataset acquisition")
    print("=" * 60)

    hillstrom_path = download_hillstrom(force=force)
    avazu_path = download_avazu(force=force)

    print("\nAcquisition complete:")
    print(f"  Hillstrom: {hillstrom_path}")
    print(f"  Avazu:     {avazu_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
