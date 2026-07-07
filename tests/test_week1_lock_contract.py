"""Week 1 data lock document and generator contract tests."""

from __future__ import annotations

import json

import pytest

import generate_week1_data_lock as week1_lock
from helpers import DOCS_DIR, PROJECT_ROOT, WEEK1_LOCKED, read_text
from paths import WEEK1_DATA_LOCK_DOC

pytestmark = [pytest.mark.week1, pytest.mark.docs, pytest.mark.unit]


LOCK_REQUIRED_STRINGS = [
    "Status:** Locked",
    "500,000",
    "64,000",
    "16.4074%",
    "14.6781%",
    "0.9031%",
    "control",
    "mens_email",
    "womens_email",
    "load_to_duckdb.py",
    "validate_data.py",
    "generate_week1_data_lock.py",
    "Week 2 boundary",
    "week2_analytics_lock.md",
]


LOCK_FORBIDDEN_STRINGS = [
    "/tmp/pytest",
    "/private/var/folders",
    "pytest-of-",
    ": 3 rows",
    ": 4 rows",
]


@pytest.mark.parametrize("term", LOCK_REQUIRED_STRINGS)
def test_week1_lock_doc_contains_required_term(term: str):
    assert term in read_text(WEEK1_DATA_LOCK_DOC)


@pytest.mark.parametrize("term", LOCK_FORBIDDEN_STRINGS)
def test_week1_lock_doc_does_not_contain_test_artifacts(term: str):
    assert term not in read_text(WEEK1_DATA_LOCK_DOC)


def test_week1_lock_doc_does_not_claim_phase3_complete():
    content = read_text(WEEK1_DATA_LOCK_DOC).lower()
    assert "tableau dashboard complete" not in content
    assert "week2_analytics_lock.md" in content


def test_generate_lock_module_has_main():
    assert hasattr(week1_lock, "main")
    assert hasattr(week1_lock, "generate_week1_data_lock")


def test_generate_lock_fails_without_summaries(tmp_path, monkeypatch):
    monkeypatch.setattr(week1_lock, "RAW_PROFILE_SUMMARY", tmp_path / "missing_profile.json")
    monkeypatch.setattr(week1_lock, "CLEANING_SUMMARY", tmp_path / "missing_cleaning.json")
    monkeypatch.setattr(week1_lock, "DUCKDB_LOAD_SUMMARY", tmp_path / "missing_load.json")
    monkeypatch.setattr(week1_lock, "DATA_VALIDATION_SUMMARY", tmp_path / "missing_validation.json")
    with pytest.raises(FileNotFoundError):
        week1_lock.generate_week1_data_lock(output_path=tmp_path / "lock.md")


def test_generate_lock_fails_when_validation_not_success(tmp_path, monkeypatch):
    processed = tmp_path / "processed"
    processed.mkdir()
    paths = {
        "profile": processed / "raw_profile_summary.json",
        "cleaning": processed / "cleaning_summary.json",
        "load": processed / "duckdb_load_summary.json",
        "validation": processed / "data_validation_summary.json",
    }
    paths["profile"].write_text(json.dumps({"datasets": {"avazu": {}, "hillstrom": {}}}))
    paths["cleaning"].write_text(json.dumps({"datasets": {"avazu": {}, "hillstrom": {}}}))
    paths["load"].write_text(json.dumps({"loads": []}))
    paths["validation"].write_text(json.dumps({"success": False}))
    monkeypatch.setattr(week1_lock, "RAW_PROFILE_SUMMARY", paths["profile"])
    monkeypatch.setattr(week1_lock, "CLEANING_SUMMARY", paths["cleaning"])
    monkeypatch.setattr(week1_lock, "DUCKDB_LOAD_SUMMARY", paths["load"])
    monkeypatch.setattr(week1_lock, "DATA_VALIDATION_SUMMARY", paths["validation"])
    with pytest.raises(RuntimeError, match="Validation summary indicates failures"):
        week1_lock.generate_week1_data_lock(output_path=tmp_path / "lock.md")


def test_locked_constants_match_document():
    content = read_text(WEEK1_DATA_LOCK_DOC)
    assert f"{WEEK1_LOCKED['avazu_rows']:,}" in content
    assert f"{WEEK1_LOCKED['hillstrom_rows']:,}" in content
    assert f"{WEEK1_LOCKED['avazu_ctr_pct']:.4f}%" in content
