"""Downloader/import script tests (no network)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

import download_or_import_data as downloader
from helpers import AVAZU_COLUMNS, tiny_avazu_rows, write_tiny_avazu_csv, write_tiny_hillstrom_csv

pytestmark = [pytest.mark.unit, pytest.mark.integration]


def test_import_hillstrom_from_path(tmp_path: Path) -> None:
    source = write_tiny_hillstrom_csv(tmp_path / "hillstrom_source.csv")
    dest = tmp_path / "raw" / "hillstrom_email.csv"
    result = downloader.import_hillstrom_from_path(source, dest)
    assert result == dest
    assert dest.exists()
    assert len(pd.read_csv(dest)) == 4


def test_import_avazu_from_path_with_sampling(tmp_path: Path) -> None:
    source = write_tiny_avazu_csv(tmp_path / "avazu_source.csv")
    dest = tmp_path / "raw" / "avazu_train.csv"
    result = downloader.import_avazu_from_path(source, dest, sample_rows=2)
    assert result == dest
    df = pd.read_csv(dest)
    assert len(df) == 2
    assert list(df.columns) == AVAZU_COLUMNS


def test_import_avazu_from_path_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        downloader.import_avazu_from_path(tmp_path / "missing.csv", tmp_path / "out.csv")


def test_download_hillstrom_skips_when_exists(tmp_path: Path, monkeypatch) -> None:
    dest = tmp_path / "hillstrom_email.csv"
    write_tiny_hillstrom_csv(dest)
    monkeypatch.setattr(downloader, "HILLSTROM_RAW_CSV", dest)

    called = {"download": False}

    def fake_download(*args, **kwargs):
        called["download"] = True

    monkeypatch.setattr(downloader, "download_file", fake_download)
    result = downloader.download_hillstrom(force=False)
    assert result == dest
    assert called["download"] is False


def test_download_avazu_skips_when_exists(tmp_path: Path, monkeypatch) -> None:
    dest = tmp_path / "avazu_train.csv"
    write_tiny_avazu_csv(dest)
    monkeypatch.setattr(downloader, "AVAZU_RAW_CSV", dest)

    called = {"dropbox": False}

    def fake_dropbox(*args, **kwargs):
        called["dropbox"] = True
        return dest

    monkeypatch.setattr(downloader, "_import_avazu_from_dropbox", fake_dropbox)
    result = downloader.download_avazu(force=False)
    assert result == dest
    assert called["dropbox"] is False


def test_sample_avazu_from_gzip(tmp_path: Path) -> None:
    import gzip

    gz_path = tmp_path / "train.gz"
    row = ",".join(str(v) for v in tiny_avazu_rows()[0].values())
    with gzip.open(gz_path, "wt") as handle:
        handle.write(row + "\n")
        handle.write(row + "\n")

    dest = tmp_path / "avazu_train.csv"
    downloader._sample_avazu_from_gzip(gz_path, dest, sample_rows=2)
    df = pd.read_csv(dest)
    assert len(df) == 2


@pytest.mark.network
def test_dropbox_url_is_defined_for_optional_network_suite() -> None:
    assert downloader.AVAZU_DROPBOX_1M_URL.startswith("https://")
