"""Requirements and dependency import tests."""

from __future__ import annotations

import importlib
import re

import pytest

from helpers import PROJECT_ROOT, REQUIRED_PACKAGES, read_text

pytestmark = pytest.mark.unit


def _package_lines() -> list[str]:
    lines = []
    for line in read_text(PROJECT_ROOT / "requirements.txt").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append(stripped)
    return lines


def test_requirements_contains_expected_packages() -> None:
    content = read_text(PROJECT_ROOT / "requirements.txt").lower()
    for package in REQUIRED_PACKAGES:
        assert package in content


def test_requirements_has_no_duplicate_package_names() -> None:
    names = []
    for line in _package_lines():
        names.append(re.split(r"[<>=!]", line)[0].strip())
    assert len(names) == len(set(names))


def test_requirements_lines_are_normalized() -> None:
    for line in _package_lines():
        assert line == line.strip()
        assert " " not in line.split(">=")[0]


@pytest.mark.parametrize("package_name", REQUIRED_PACKAGES)
def test_required_package_imports(package_name: str) -> None:
    importlib.import_module(package_name)
