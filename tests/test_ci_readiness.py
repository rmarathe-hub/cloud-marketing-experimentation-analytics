"""CI readiness tests for default pytest execution."""

from __future__ import annotations

import subprocess

import pytest

from helpers import PROJECT_ROOT, read_text

pytestmark = [pytest.mark.unit, pytest.mark.week1]


def test_no_github_actions_workflow_present():
    workflows = list((PROJECT_ROOT / ".github" / "workflows").glob("*.yml")) if (
        PROJECT_ROOT / ".github" / "workflows"
    ).exists() else []
    assert workflows == []


def test_pytest_ini_excludes_network_and_aws_by_default():
    ini = read_text(PROJECT_ROOT / "pytest.ini")
    assert 'addopts = -m "not network and not aws"' in ini


def test_default_pytest_collection_succeeds():
    result = subprocess.run(
        ["python", "-m", "pytest", "--collect-only", "-q"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "test session starts" in (result.stdout + result.stderr).lower() or "tests collected" in (result.stdout + result.stderr).lower()


@pytest.mark.parametrize(
    "marker",
    ["unit", "docs", "hygiene", "cleaning", "profiling", "smoke", "duckdb", "s3", "security", "week1"],
)
def test_marker_registered(marker: str):
    ini = read_text(PROJECT_ROOT / "pytest.ini")
    assert f"{marker}:" in ini
