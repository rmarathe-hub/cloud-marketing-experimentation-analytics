"""Extended .gitignore contract tests."""

from __future__ import annotations

import pytest

from helpers import GITIGNORE_REQUIRED_FRAGMENTS, PROJECT_ROOT, read_text

pytestmark = [pytest.mark.hygiene, pytest.mark.unit]

EXTRA_GITIGNORE_FRAGMENTS = [
    "data/raw/*",
    "data/processed/*",
    "data/marts/*",
    "data/exports/*",
    "excel/*.xlsx",
    "excel/*.xlsm",
    "*.twbx",
    "*.twb",
    ".pytest_cache/",
]


@pytest.mark.parametrize("fragment", GITIGNORE_REQUIRED_FRAGMENTS)
def test_gitignore_contains_required_fragment(fragment: str):
    assert fragment in read_text(PROJECT_ROOT / ".gitignore")


@pytest.mark.parametrize("fragment", EXTRA_GITIGNORE_FRAGMENTS)
def test_gitignore_protects_generated_artifacts(fragment: str):
    assert fragment in read_text(PROJECT_ROOT / ".gitignore")


def test_gitignore_keeps_tableau_screenshot_directory_exception():
    gitignore = read_text(PROJECT_ROOT / ".gitignore")
    assert "tableau/screenshots" in gitignore or "!tableau/screenshots" in gitignore
