"""Safety tests (135E §25, §28's structural claims re-verified).

Verifies, by import-graph and source inspection, that the CLTR prototype
package has no code path to shell execution, backend invocation, network
calls, Telegram delivery, phase completion, commit, push, Decision
Evaluation, or execution authorization, and that its only write path is
`persistence.py`'s hardcoded `.pcae/cltr-prototypes/` prefix.
"""

from __future__ import annotations

import ast
import importlib
import json
import pkgutil
from pathlib import Path

import pytest

import pcae.cltr_prototype as pkg
from pcae.cltr_prototype import generator, persistence

FIXTURES = Path(__file__).parent / "fixtures" / "cltr_prototype"
PACKAGE_ROOT = Path(pkg.__file__).parent


def _all_module_names():
    names = []
    for module_info in pkgutil.iter_modules([str(PACKAGE_ROOT)]):
        names.append(f"pcae.cltr_prototype.{module_info.name}")
    return names


@pytest.mark.parametrize("module_name", _all_module_names())
def test_no_subprocess_or_network_imports(module_name):
    module = importlib.import_module(module_name)
    source = Path(module.__file__).read_text()
    tree = ast.parse(source)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    forbidden = {"subprocess", "socket", "requests", "httpx", "urllib"}
    assert not (imported & forbidden), f"{module_name} imports forbidden module(s): {imported & forbidden}"


@pytest.mark.parametrize("module_name", _all_module_names())
def test_no_production_finalization_import(module_name):
    module = importlib.import_module(module_name)
    source = Path(module.__file__).read_text()
    assert "finalization_transaction" not in source
    assert "canonical_artifact_promotion" not in source


def test_production_finalization_does_not_import_prototype():
    finalization_path = Path(pkg.__file__).parent.parent / "core" / "finalization_transaction.py"
    if finalization_path.exists():
        source = finalization_path.read_text()
        assert "cltr_prototype" not in source


def test_no_telegram_or_notification_sink_import():
    for module_name in _all_module_names():
        module = importlib.import_module(module_name)
        source = Path(module.__file__).read_text()
        assert "telegram" not in source.lower()
        assert "notification_config" not in source
        assert "notification_sink" not in source


def test_no_decision_evaluation_import():
    for module_name in _all_module_names():
        module = importlib.import_module(module_name)
        source = Path(module.__file__).read_text()
        assert "decision_log" not in source
        assert "decision_evaluation" not in source


def test_no_repository_intelligence_import():
    for module_name in _all_module_names():
        module = importlib.import_module(module_name)
        source = Path(module.__file__).read_text()
        assert "repository_intelligence" not in source


def test_only_persistence_module_writes_files():
    write_indicators = ("open(", ".write_text(", ".write_bytes(", "os.replace", "mkstemp", "NamedTemporaryFile")
    for module_name in _all_module_names():
        if module_name.endswith(".persistence"):
            continue
        module = importlib.import_module(module_name)
        source = Path(module.__file__).read_text()
        for indicator in write_indicators:
            assert indicator not in source, f"{module_name} unexpectedly contains a write indicator: {indicator!r}"


def test_persistence_write_path_hardcoded_to_prototype_prefix():
    source = Path(persistence.__file__).read_text()
    assert 'PROTOTYPE_DIR_NAME = ".pcae/cltr-prototypes"' in source


def test_full_run_touches_no_production_artifact(tmp_path):
    fixture = json.loads((FIXTURES / "successful_transition.json").read_text())
    result = generator.generate(fixture)
    persistence.persist(result.record, result.invariant_results, base_dir=tmp_path)

    for forbidden_name in (
        "canonical-reports",
        "phase-completion-metadata.json",
        "phase-completion-report.md",
        "finalization-transactions",
        "delivery-receipts",
    ):
        matches = list(tmp_path.rglob(f"*{forbidden_name}*"))
        assert matches == [], f"unexpected production-shaped path created: {matches}"


def test_no_execution_authorization_field_anywhere():
    for module_name in _all_module_names():
        module = importlib.import_module(module_name)
        tree = ast.parse(Path(module.__file__).read_text())
        assigned_or_called_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                assigned_or_called_names.add(node.attr)
            if isinstance(node, ast.Name):
                assigned_or_called_names.add(node.id)
        assert "may_execute" not in assigned_or_called_names
        assert "authorize_execution" not in assigned_or_called_names
