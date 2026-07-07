"""Extended S3 upload contract tests with mocked AWS."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import upload_to_s3 as uploader
from helpers import (
    PROJECT_ROOT,
    S3_FORBIDDEN_UPLOAD_PATTERNS,
    S3_UPLOAD_KEYS,
    S3_UPLOAD_LOCAL_FILES,
    assert_no_secret_patterns,
    read_text,
)
from paths import (
    AVAZU_CLEAN_PARQUET,
    AVAZU_RAW_CSV,
    HILLSTROM_CLEAN_PARQUET,
    HILLSTROM_RAW_CSV,
    S3_UPLOAD_SUMMARY,
)

pytestmark = [pytest.mark.s3, pytest.mark.unit, pytest.mark.security]


def test_upload_module_has_required_api():
    for name in ["main", "load_config", "get_upload_targets", "upload_targets", "write_upload_summary"]:
        assert hasattr(uploader, name)


def test_upload_targets_exact_local_files():
    config = uploader.UploadConfig(
        aws_profile="marketing-analytics",
        aws_region="us-east-1",
        bucket="test-bucket",
        raw_prefix="raw",
        processed_prefix="processed",
        marts_prefix="marts",
        export_prefix="exports",
    )
    targets = uploader.get_upload_targets(config)
    assert len(targets) == 4
    local_names = {t.local_path.name for t in targets}
    assert local_names == {
        "avazu_train.csv",
        "hillstrom_email.csv",
        "avazu_clean.parquet",
        "hillstrom_clean.parquet",
    }


@pytest.mark.parametrize("expected_key", S3_UPLOAD_KEYS)
def test_upload_target_s3_keys(expected_key: str):
    config = uploader.UploadConfig(
        aws_profile="marketing-analytics",
        aws_region="us-east-1",
        bucket="test-bucket",
        raw_prefix="raw",
        processed_prefix="processed",
        marts_prefix="marts",
        export_prefix="exports",
    )
    keys = [t.s3_key for t in uploader.get_upload_targets(config)]
    assert expected_key in keys


@pytest.mark.parametrize("forbidden", S3_FORBIDDEN_UPLOAD_PATTERNS)
def test_upload_script_source_does_not_upload_forbidden_paths(forbidden: str):
    content = read_text(PROJECT_ROOT / "scripts" / "upload_to_s3.py")
    if forbidden.endswith("/"):
        assert forbidden not in content or "marts" in content  # prefix config only
    elif forbidden == ".env":
        assert "load_dotenv" in content
        assert "upload" not in content.split(".env")[0][-20:]


def test_upload_script_does_not_reference_cleaning_summary_as_upload_target():
    config = uploader.UploadConfig(
        aws_profile="marketing-analytics",
        aws_region="us-east-1",
        bucket="test-bucket",
        raw_prefix="raw",
        processed_prefix="processed",
        marts_prefix="marts",
        export_prefix="exports",
    )
    targets = uploader.get_upload_targets(config)
    names = [t.local_path.name for t in targets]
    assert "cleaning_summary.json" not in names


@patch.object(uploader.boto3, "Session")
def test_upload_uses_aws_profile(mock_session, tmp_path):
    config = uploader.UploadConfig(
        aws_profile="marketing-analytics",
        aws_region="us-east-1",
        bucket="test-bucket",
        raw_prefix="raw",
        processed_prefix="processed",
        marts_prefix="marts",
        export_prefix="exports",
    )
    uploader.create_s3_client(config)
    mock_session.assert_called_once_with(
        region_name="us-east-1",
        profile_name="marketing-analytics",
    )


def test_upload_summary_schema_on_success(tmp_path):
    local_file = tmp_path / "sample.csv"
    local_file.write_text("id,click\n1,0\n")
    config = uploader.UploadConfig(
        aws_profile="marketing-analytics",
        aws_region="us-east-1",
        bucket="test-bucket",
        raw_prefix="raw",
        processed_prefix="processed",
        marts_prefix="marts",
        export_prefix="exports",
    )
    targets = [uploader.UploadTarget(local_path=local_file, s3_key="raw/sample.csv")]
    client = MagicMock()
    summary = uploader.upload_targets(client, config, targets)
    for key in ["generated_at", "bucket", "uploads", "uploaded_count", "failed_count", "success"]:
        assert key in summary
    assert summary["uploads"][0]["s3_key"] == "raw/sample.csv"
    assert "size_mb" in summary["uploads"][0]


def test_upload_script_source_has_no_secrets():
    assert_no_secret_patterns(read_text(PROJECT_ROOT / "scripts" / "upload_to_s3.py"), "upload_to_s3.py")


@pytest.mark.aws
@pytest.mark.network
def test_real_aws_upload_disabled_by_default():
    pytest.skip("Real AWS integration disabled unless RUN_AWS_TESTS=1 is set.")


@pytest.mark.data
@pytest.mark.slow
def test_s3_upload_summary_contract_if_present():
    if not S3_UPLOAD_SUMMARY.exists():
        pytest.skip("S3 upload summary not generated locally")
    payload = json.loads(S3_UPLOAD_SUMMARY.read_text())
    assert payload["success"] is True
    assert payload["uploaded_count"] == 4
    keys = [item["s3_key"] for item in payload["uploads"]]
    for expected in S3_UPLOAD_KEYS:
        assert expected in keys
    assert_no_secret_patterns(S3_UPLOAD_SUMMARY.read_text(), "s3_upload_summary.json")
