"""upload_to_s3.py tests with mocked AWS calls."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import upload_to_s3 as uploader
from helpers import PROJECT_ROOT, read_text
from paths import (
    AVAZU_CLEAN_PARQUET,
    AVAZU_RAW_CSV,
    HILLSTROM_CLEAN_PARQUET,
    HILLSTROM_RAW_CSV,
    S3_UPLOAD_SUMMARY,
)

pytestmark = pytest.mark.unit


def test_upload_module_imports_without_aws_calls():
    assert hasattr(uploader, "main")
    assert hasattr(uploader, "load_config")
    assert hasattr(uploader, "get_upload_targets")


def test_load_config_reads_env_and_profile(monkeypatch):
    monkeypatch.setenv("AWS_PROFILE", "marketing-analytics")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("S3_BUCKET", "test-bucket-123")
    monkeypatch.setenv("S3_RAW_PREFIX", "raw")
    monkeypatch.setenv("S3_PROCESSED_PREFIX", "processed")

    config = uploader.load_config()

    assert config.aws_profile == "marketing-analytics"
    assert config.aws_region == "us-east-1"
    assert config.bucket == "test-bucket-123"
    assert config.raw_prefix == "raw"
    assert config.processed_prefix == "processed"


def test_load_config_missing_bucket_raises(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("AWS_REGION=us-east-1\n")
    monkeypatch.delenv("S3_BUCKET", raising=False)

    with pytest.raises(ValueError, match="S3_BUCKET"):
        uploader.load_config(env_path=env_file)


def test_load_config_placeholder_bucket_raises(monkeypatch):
    monkeypatch.setenv("S3_BUCKET", "your-bucket-name")
    monkeypatch.setenv("AWS_REGION", "us-east-1")

    with pytest.raises(ValueError, match="S3_BUCKET is not configured"):
        uploader.load_config()


def test_get_upload_targets_keys():
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
    keys = [target.s3_key for target in targets]
    local_paths = [target.local_path for target in targets]

    assert keys == [
        "raw/avazu_train.csv",
        "raw/hillstrom_email.csv",
        "processed/avazu_clean.parquet",
        "processed/hillstrom_clean.parquet",
    ]
    assert local_paths == [
        AVAZU_RAW_CSV,
        HILLSTROM_RAW_CSV,
        AVAZU_CLEAN_PARQUET,
        HILLSTROM_CLEAN_PARQUET,
    ]


def test_validate_local_files_missing(tmp_path, monkeypatch):
    missing = tmp_path / "missing.csv"
    targets = [uploader.UploadTarget(local_path=missing, s3_key="raw/missing.csv")]

    with pytest.raises(FileNotFoundError, match="Missing required local files"):
        uploader.validate_local_files(targets)


def test_verify_bucket_access_missing_bucket():
    client = MagicMock()
    error = uploader.ClientError(
        {"Error": {"Code": "404", "Message": "Not Found"}},
        "HeadBucket",
    )
    client.head_bucket.side_effect = error

    with pytest.raises(RuntimeError, match="bucket not found"):
        uploader.verify_bucket_access(client, "missing-bucket")


def test_verify_bucket_access_denied():
    client = MagicMock()
    error = uploader.ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "Denied"}},
        "HeadBucket",
    )
    client.head_bucket.side_effect = error

    with pytest.raises(RuntimeError, match="Access denied"):
        uploader.verify_bucket_access(client, "secret-bucket")


@patch.object(uploader.boto3, "Session")
def test_create_s3_client_uses_profile(mock_session):
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


def test_upload_targets_calls_upload_file(tmp_path):
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

    client.upload_file.assert_called_once_with(
        Filename=str(local_file),
        Bucket="test-bucket",
        Key="raw/sample.csv",
    )
    assert summary["success"] is True
    assert summary["uploaded_count"] == 1
    assert summary["uploads"][0]["s3_key"] == "raw/sample.csv"


def test_write_upload_summary_schema(tmp_path):
    summary = {
        "generated_at": "2026-01-01T00:00:00+00:00",
        "bucket": "test-bucket",
        "aws_region": "us-east-1",
        "aws_profile": "marketing-analytics",
        "prefixes": {"raw": "raw", "processed": "processed", "marts": "marts", "exports": "exports"},
        "uploads": [
            {
                "local_file": "data/raw/sample.csv",
                "s3_uri": "s3://test-bucket/raw/sample.csv",
                "s3_key": "raw/sample.csv",
                "size_mb": 0.01,
                "status": "success",
                "error": None,
            }
        ],
        "uploaded_count": 1,
        "failed_count": 0,
        "success": True,
    }

    output = tmp_path / "s3_upload_summary.json"
    uploader.write_upload_summary(summary, output)

    payload = json.loads(output.read_text())
    assert payload["success"] is True
    assert payload["bucket"] == "test-bucket"
    assert payload["uploads"][0]["status"] == "success"


def test_aws_s3_setup_doc_exists_with_security_warnings():
    content = read_text(PROJECT_ROOT / "docs" / "aws_s3_setup.md").lower()
    for term in [
        "block public access",
        "never commit",
        "budget",
        "glue",
        "lambda",
        "ec2",
        "redshift",
        "athena",
        "marketing-analytics",
    ]:
        assert term in content


def test_readme_does_not_claim_week2_marts_complete():
    readme = read_text(PROJECT_ROOT / "README.md")
    assert "DuckDB load + validation | ✅ Complete" in readme
    assert "Campaign KPI marts | ✅ Complete" in readme
    assert "Funnel + segment analysis | ✅ Complete" in readme
    assert "A/B test analysis | ✅ Complete" in readme
    assert "CTR forecasting | ✅ Complete" in readme
    assert "Tableau dashboard | 🔲 Pending" in readme


def test_upload_script_does_not_contain_secrets():
    content = read_text(PROJECT_ROOT / "scripts" / "upload_to_s3.py")
    assert "AKIA" not in content
    assert "aws_secret_access_key" not in content.lower()


@pytest.mark.aws
@pytest.mark.integration
def test_real_aws_upload_requires_explicit_enable():
    pytest.skip("Real AWS upload tests are disabled by default. Use mocks in normal pytest runs.")
