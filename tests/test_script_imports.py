"""Script import safety tests."""

from __future__ import annotations

import importlib
import sys

import pytest

from helpers import PROJECT_ROOT, REQUIRED_SCRIPTS

pytestmark = pytest.mark.unit

SCRIPT_MODULES = [name.replace(".py", "") for name in REQUIRED_SCRIPTS]


@pytest.mark.parametrize("module_name", SCRIPT_MODULES)
def test_script_imports_without_side_effects(module_name: str) -> None:
    if module_name in sys.modules:
        del sys.modules[module_name]
    module = importlib.import_module(module_name)
    assert module is not None


@pytest.mark.parametrize("module_name", SCRIPT_MODULES)
def test_script_has_main_or_callable_entrypoint(module_name: str) -> None:
    module = importlib.import_module(module_name)
    if module_name in {"paths", "cleaning_utils"}:
        pytest.skip(f"{module_name} is a helper module without CLI entrypoint")
    assert hasattr(module, "main")
    assert callable(module.main)


def test_scripts_do_not_embed_credentials() -> None:
    for script_name in REQUIRED_SCRIPTS:
        content = (PROJECT_ROOT / "scripts" / script_name).read_text(encoding="utf-8")
        assert "AKIA" not in content
        assert "KAGGLE_KEY=" not in content or "your_kaggle" in content
        assert "aws_secret_access_key" not in content.lower()
