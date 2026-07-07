"""Extended requirements.txt contract tests."""

from __future__ import annotations

import importlib

import pytest

from helpers import PROJECT_ROOT, REQUIRED_PACKAGES, read_text

pytestmark = [pytest.mark.unit, pytest.mark.week1]


def test_requirements_file_exists():
    assert (PROJECT_ROOT / "requirements.txt").is_file()


def test_requirements_has_no_duplicate_package_names():
    lines = [
        line.strip()
        for line in read_text(PROJECT_ROOT / "requirements.txt").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    names = [line.split(">=")[0].split("==")[0].strip().lower() for line in lines]
    assert len(names) == len(set(names))


@pytest.mark.parametrize("package_name", REQUIRED_PACKAGES)
def test_required_package_importable(package_name: str):
    importlib.import_module(package_name)


@pytest.mark.parametrize("package_name", REQUIRED_PACKAGES)
def test_required_package_listed_in_requirements(package_name: str):
    requirements = read_text(PROJECT_ROOT / "requirements.txt").lower()
    lookup = "python-dotenv" if package_name == "dotenv" else package_name
    assert lookup in requirements


def test_requirements_has_no_obvious_junk_lines():
    for line in read_text(PROJECT_ROOT / "requirements.txt").splitlines():
        if line.strip() and not line.strip().startswith("#"):
            assert ">=" in line or "==" in line
