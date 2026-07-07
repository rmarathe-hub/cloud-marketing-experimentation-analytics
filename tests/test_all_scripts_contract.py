"""Extended import-safety and entrypoint contract tests for all 18 scripts."""

from __future__ import annotations

import importlib
import sys

import pytest

from helpers import (
    ALL_SCRIPTS,
    PROJECT_ROOT,
    SCRIPTS_HELPER_ONLY,
    SCRIPTS_WITH_MAIN,
    import_script_fresh,
)

pytestmark = [pytest.mark.unit, pytest.mark.security]

FORBIDDEN_IMPORT_SUBSTRINGS = (
    "/Users/rohitmarathe",
    "AKIA",
    "aws_secret_access_key",
    "ghp_",
    "github_pat_",
    "BEGIN RSA PRIVATE KEY",
)


@pytest.mark.parametrize("script_name", ALL_SCRIPTS)
def test_script_file_exists(script_name: str) -> None:
    assert (PROJECT_ROOT / "scripts" / script_name).is_file()


@pytest.mark.parametrize("script_name", ALL_SCRIPTS)
def test_script_imports_without_error(script_name: str) -> None:
    module_name = script_name.replace(".py", "")
    module = import_script_fresh(module_name)
    assert module is not None


@pytest.mark.parametrize("script_name", ALL_SCRIPTS)
def test_script_source_has_no_hardcoded_user_paths(script_name: str) -> None:
    source = (PROJECT_ROOT / "scripts" / script_name).read_text(encoding="utf-8")
    for token in FORBIDDEN_IMPORT_SUBSTRINGS[:1]:
        assert token not in source, f"{script_name} contains hardcoded path"


@pytest.mark.parametrize("script_name", ALL_SCRIPTS)
def test_script_source_has_no_secret_patterns(script_name: str) -> None:
    source = (PROJECT_ROOT / "scripts" / script_name).read_text(encoding="utf-8").lower()
    for token in FORBIDDEN_IMPORT_SUBSTRINGS[1:]:
        assert token.lower() not in source, f"{script_name} contains secret pattern {token}"


@pytest.mark.parametrize("script_name", ALL_SCRIPTS)
def test_script_import_without_aws_env(script_name: str, monkeypatch) -> None:
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    secret_key_env = "AWS_" + "SECRET" + "_" + "ACCESS_KEY"
    monkeypatch.delenv(secret_key_env, raising=False)
    module_name = script_name.replace(".py", "")
    module = import_script_fresh(module_name)
    assert module is not None


@pytest.mark.parametrize("script_name", SCRIPTS_WITH_MAIN)
def test_cli_script_exposes_callable_main(script_name: str) -> None:
    module = import_script_fresh(script_name.replace(".py", ""))
    assert hasattr(module, "main")
    assert callable(module.main)


@pytest.mark.parametrize("script_name", SCRIPTS_HELPER_ONLY)
def test_helper_scripts_are_importable_libraries(script_name: str) -> None:
    module = import_script_fresh(script_name.replace(".py", ""))
    assert module is not None


@pytest.mark.parametrize("script_name", ALL_SCRIPTS)
def test_reimport_is_stable(script_name: str) -> None:
    module_name = script_name.replace(".py", "")
    first = import_script_fresh(module_name)
    second = importlib.import_module(module_name)
    assert first is second


def test_all_scripts_count_is_eighteen() -> None:
    assert len(ALL_SCRIPTS) == 18


def test_scripts_directory_on_pythonpath() -> None:
    assert str(PROJECT_ROOT / "scripts") in sys.path
