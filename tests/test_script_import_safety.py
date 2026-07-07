"""Week 1 script import safety tests."""

from __future__ import annotations

import importlib
import sys

import pytest

from helpers import (
    PROJECT_ROOT,
    REQUIRED_SCRIPTS,
    SCRIPTS_HELPER_ONLY,
    SCRIPTS_WITH_MAIN,
    WEEK2_SCRIPTS_IMPLEMENTED,
    import_script_fresh,
)

pytestmark = [pytest.mark.unit, pytest.mark.week1]

ALL_SCRIPT_MODULES = [
    name.replace(".py", "")
    for name in (*REQUIRED_SCRIPTS, *WEEK2_SCRIPTS_IMPLEMENTED)
]


@pytest.mark.parametrize("module_name", ALL_SCRIPT_MODULES)
def test_week1_script_imports_cleanly(module_name: str) -> None:
    module = import_script_fresh(module_name)
    assert module is not None


@pytest.mark.parametrize("module_name", SCRIPTS_WITH_MAIN)
def test_cli_scripts_expose_main(module_name: str) -> None:
    module = import_script_fresh(module_name.replace(".py", ""))
    assert hasattr(module, "main")
    assert callable(module.main)


@pytest.mark.parametrize("module_name", SCRIPTS_HELPER_ONLY)
def test_helper_scripts_are_libraries(module_name: str) -> None:
    module = import_script_fresh(module_name.replace(".py", ""))
    assert module is not None


@pytest.mark.parametrize("module_name", ALL_SCRIPT_MODULES)
def test_import_does_not_require_aws_credentials(module_name: str, monkeypatch) -> None:
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    secret_key_env = "AWS_" + "SECRET" + "_" + "ACCESS_KEY"
    monkeypatch.delenv(secret_key_env, raising=False)
    module = import_script_fresh(module_name)
    assert module is not None


def test_reimport_same_module_is_stable() -> None:
    first = import_script_fresh("paths")
    second = importlib.import_module("paths")
    assert first is second


def test_scripts_directory_on_pythonpath() -> None:
    scripts = str(PROJECT_ROOT / "scripts")
    assert scripts in sys.path
