""".env.example and environment placeholder contract tests."""

from __future__ import annotations

import pytest

from helpers import PLACEHOLDER_ENV_VALUES, PROJECT_ROOT, assert_no_secret_patterns, read_text

pytestmark = [pytest.mark.security, pytest.mark.hygiene, pytest.mark.unit]


def test_env_example_exists():
    assert (PROJECT_ROOT / ".env.example").is_file()


def test_env_example_uses_placeholder_bucket():
    content = read_text(PROJECT_ROOT / ".env.example")
    assert "your-bucket-name" in content


def test_env_example_sets_marketing_analytics_profile():
    content = read_text(PROJECT_ROOT / ".env.example")
    assert "AWS_PROFILE=marketing-analytics" in content


def test_env_example_has_s3_prefixes():
    content = read_text(PROJECT_ROOT / ".env.example")
    for prefix in ("S3_RAW_PREFIX", "S3_PROCESSED_PREFIX", "S3_MARTS_PREFIX", "S3_EXPORT_PREFIX"):
        assert prefix in content


def test_env_example_has_duckdb_path():
    assert "DUCKDB_PATH" in read_text(PROJECT_ROOT / ".env.example")


@pytest.mark.parametrize("placeholder", sorted(PLACEHOLDER_ENV_VALUES))
def test_env_example_contains_expected_placeholder(placeholder: str):
    assert placeholder in read_text(PROJECT_ROOT / ".env.example")


def test_env_example_has_no_secret_patterns():
    assert_no_secret_patterns(read_text(PROJECT_ROOT / ".env.example"), ".env.example")


def test_env_file_is_gitignored():
    gitignore = read_text(PROJECT_ROOT / ".gitignore")
    assert ".env" in gitignore
