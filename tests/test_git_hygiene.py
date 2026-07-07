"""Git hygiene and secret protection tests."""

from __future__ import annotations

import re

import pytest

from helpers import (
    PLACEHOLDER_ENV_VALUES,
    PROJECT_ROOT,
    SECRET_PATTERNS,
    git_tracked_files,
    read_text,
)

pytestmark = [pytest.mark.unit, pytest.mark.hygiene]


TRACKED = git_tracked_files()


@pytest.mark.parametrize(
    "pattern",
    [
        r"^data/raw/.+\.(csv|parquet|json)$",
        r"^data/processed/.+\.(csv|parquet|json)$",
        r"^data/marts/.+\.csv$",
        r"^data/exports/.+\.csv$",
        r"^\.env$",
        r"^\.venv/",
        r"__pycache__",
        r"\.DS_Store$",
        r"\.duckdb$",
        r"\.twbx$",
        r"excel/.+\.xlsx$",
    ],
)
def test_no_tracked_sensitive_or_data_files(pattern: str) -> None:
    regex = re.compile(pattern)
    matches = [path for path in TRACKED if regex.search(path)]
    assert matches == [], f"Unexpected tracked files: {matches}"


def test_gitignore_protects_env_and_data() -> None:
    gitignore = read_text(PROJECT_ROOT / ".gitignore")
    required_fragments = [
        ".env",
        ".venv/",
        "__pycache__/",
        "data/raw/*",
        "data/processed/*",
        "data/marts/*",
        "data/exports/*",
        "*.duckdb",
        ".DS_Store",
        "excel/*.xlsx",
        "*.twbx",
    ]
    for fragment in required_fragments:
        assert fragment in gitignore


def test_env_example_has_placeholders_only() -> None:
    env_example = read_text(PROJECT_ROOT / ".env.example")
    for placeholder in PLACEHOLDER_ENV_VALUES:
        assert placeholder in env_example
    assert "AKIA" not in env_example
    assert "ghp_" not in env_example


@pytest.mark.parametrize("tracked_file", TRACKED)
def test_tracked_files_do_not_contain_secret_patterns(tracked_file: str) -> None:
    path = PROJECT_ROOT / tracked_file
    if not path.is_file() or path.suffix not in {".py", ".md", ".txt", ".example", ".ini", ""}:
        pytest.skip("Non-text tracked file")
    content = read_text(path)
    lowered = content.lower()
    for pattern in SECRET_PATTERNS:
        assert pattern.lower() not in lowered, f"{tracked_file} contains {pattern}"


def test_no_hardcoded_user_paths_in_scripts() -> None:
    scripts_dir = PROJECT_ROOT / "scripts"
    for script in scripts_dir.glob("*.py"):
        content = read_text(script)
        assert "/Users/" not in content
        assert "C:\\Users\\" not in content
