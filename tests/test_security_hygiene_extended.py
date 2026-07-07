"""Extended repository hygiene and secret protection tests."""

from __future__ import annotations

import re

import pytest

from helpers import (
    GITIGNORE_REQUIRED_FRAGMENTS,
    PLACEHOLDER_ENV_VALUES,
    PROJECT_ROOT,
    SCRIPTS_DIR,
    SECRET_PATTERNS,
    SECRET_PATTERN_SCAN_EXEMPT,
    TRACKED_FORBIDDEN_PATTERNS,
    assert_no_secret_patterns,
    git_tracked_files,
    read_text,
)

pytestmark = [pytest.mark.hygiene, pytest.mark.security, pytest.mark.unit]

TRACKED = git_tracked_files()


@pytest.mark.parametrize("pattern", TRACKED_FORBIDDEN_PATTERNS)
def test_no_tracked_forbidden_paths(pattern: str) -> None:
    regex = re.compile(pattern)
    matches = [path for path in TRACKED if regex.search(path)]
    assert matches == [], f"Unexpected tracked files: {matches}"


@pytest.mark.parametrize("fragment", GITIGNORE_REQUIRED_FRAGMENTS)
def test_gitignore_contains_required_fragment(fragment: str) -> None:
    assert fragment in read_text(PROJECT_ROOT / ".gitignore")


def test_env_example_uses_placeholders_only() -> None:
    env_example = read_text(PROJECT_ROOT / ".env.example")
    for placeholder in PLACEHOLDER_ENV_VALUES:
        assert placeholder in env_example
    assert_no_secret_patterns(env_example, ".env.example")


@pytest.mark.parametrize("tracked_file", TRACKED)
def test_tracked_text_files_have_no_secrets(tracked_file: str) -> None:
    if tracked_file in SECRET_PATTERN_SCAN_EXEMPT:
        pytest.skip("Intentional secret-pattern references for detection tests")
    path = PROJECT_ROOT / tracked_file
    if not path.is_file() or path.suffix not in {".py", ".md", ".txt", ".example", ".ini", ""}:
        pytest.skip("Non-text tracked file")
    assert_no_secret_patterns(read_text(path), tracked_file)


@pytest.mark.parametrize("script_name", [p.name for p in SCRIPTS_DIR.glob("*.py")])
def test_scripts_have_no_hardcoded_user_paths(script_name: str) -> None:
    content = read_text(SCRIPTS_DIR / script_name)
    assert "/Users/" not in content
    assert "C:\\Users\\" not in content


@pytest.mark.parametrize("script_name", [p.name for p in SCRIPTS_DIR.glob("*.py")])
def test_scripts_have_no_hardcoded_credentials(script_name: str) -> None:
    if script_name in {"upload_to_s3.py"}:
        pytest.skip("Checked in dedicated S3 tests")
    content = read_text(SCRIPTS_DIR / script_name)
    for pattern in SECRET_PATTERNS:
        if pattern in {"AKIA", "aws_secret_access_key"}:
            assert pattern.lower() not in content.lower()


@pytest.mark.parametrize(
    "doc_name",
    [
        "aws_s3_setup.md",
        "cost_controls.md",
        "week1_data_lock.md",
        "duckdb_setup.md",
    ],
)
def test_security_docs_warn_about_credentials(doc_name: str) -> None:
    content = read_text(PROJECT_ROOT / "docs" / doc_name).lower()
    assert "credential" in content or "never commit" in content or "gitignore" in content


def test_docs_do_not_contain_private_key_blocks() -> None:
    for doc in (PROJECT_ROOT / "docs").glob("*.md"):
        content = read_text(doc)
        assert "BEGIN RSA PRIVATE KEY" not in content
        assert "BEGIN OPENSSH PRIVATE KEY" not in content
