"""Tests for Phase 109C — Observation Integration Hardening & Multi-Path
Expansion.

Verifies the expanded observation-only Permission Broker integration:
`pcae check` (INT-002), `pcae doctor task-memory` (INT-003), and
`pcae push check` (INT-004) each consult the broker, but their decisions
are provably discarded — output, exit code, and control flow are
identical regardless of what the broker returns, including if it raises.
Also verifies the new Integration ID registry and that the prior
observation path (`pcae health`, INT-001, Phase 109B) remains unchanged.

Pure in-process where possible (direct `main()` calls with `capsys`),
pytest-xdist safe. Each test that needs a working repository uses its
own isolated `tmp_path` git+PCAE scaffold — no shared `.pcae/` state.
"""

from __future__ import annotations

import inspect
import json
import subprocess
from pathlib import Path

import pytest

from pcae.cli import main
from pcae.core.command_path_observation import (
    INTEGRATION_IDS,
    INTEGRATION_REGISTRY,
    IntegrationRegistryEntry,
    get_integration,
    observe,
)
from pcae.core.paths import HarnessPath
from pcae.core.permission_broker_foundation import (
    DECISION_ALLOW,
    DECISION_DENY,
    DECISION_HUMAN_REVIEW,
    PermissionBrokerDecision,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

EXPECTED_INTEGRATIONS = {
    "INT-001": "pcae health",
    "INT-002": "pcae check",
    "INT-003": "pcae doctor task-memory",
    "INT-004": "pcae push check",
}


def _init_governed_repo(root: Path) -> None:
    """Minimal git + PCAE scaffold so the integrated commands succeed."""
    from pcae.commands.init import init_harness

    subprocess.run(["git", "init", "-q"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True, capture_output=True)
    init_harness(HarnessPath(root))


def _fake_decision(decision: str) -> PermissionBrokerDecision:
    return PermissionBrokerDecision(
        decision=decision,
        decision_reason="test_fixture",
        matched_no_go_ids=(),
        matched_invariants=(),
        required_remediation=(),
        requires_human=False,
        simulation_only=True,
    )


# ═══════════════════════════════════════════════════════════════════════
# Integration ID registry
# ═══════════════════════════════════════════════════════════════════════


def test_integration_registry_exists():
    assert INTEGRATION_REGISTRY is not None
    assert len(INTEGRATION_REGISTRY) == 4


@pytest.mark.parametrize("integration_id,command", list(EXPECTED_INTEGRATIONS.items()))
def test_integration_id_registered_with_expected_command(integration_id, command):
    entry = get_integration(integration_id)
    assert entry is not None
    assert entry.command == command


def test_integration_ids_stable_and_ordered():
    assert tuple(e.integration_id for e in INTEGRATION_REGISTRY) == ("INT-001", "INT-002", "INT-003", "INT-004")


def test_integration_ids_frozenset_matches_registry():
    assert INTEGRATION_IDS == frozenset(EXPECTED_INTEGRATIONS)


def test_unknown_integration_id_returns_none():
    assert get_integration("INT-999") is None


@pytest.mark.parametrize("entry", INTEGRATION_REGISTRY)
def test_every_integration_entry_has_required_fields(entry):
    assert entry.integration_id
    assert entry.command
    assert entry.integration_type == "observation-only"
    assert entry.observation_status == "active"
    assert entry.implementation_status == "observation_only"
    assert entry.future_evolution


def test_integration_registry_entry_is_frozen_dataclass():
    entry = INTEGRATION_REGISTRY[0]
    with pytest.raises(Exception):
        entry.integration_id = "INT-999"  # type: ignore[misc]


def test_push_check_integration_scoped_not_push_itself():
    entry = get_integration("INT-004")
    assert entry.command == "pcae push check"
    assert entry.command != "pcae push"


# ═══════════════════════════════════════════════════════════════════════
# Broker consulted by each integrated command
# ═══════════════════════════════════════════════════════════════════════


def test_check_consults_the_broker(tmp_path, monkeypatch, capsys):
    _init_governed_repo(tmp_path)
    calls = []
    monkeypatch.setattr("pcae.commands.check.observe", lambda **kw: calls.append(kw))
    monkeypatch.chdir(tmp_path)

    main(["check"])

    assert len(calls) == 1
    assert calls[0]["requested_capability"] == "pcae_check"
    assert calls[0]["requested_component"] == "COMP-001"


def test_doctor_task_memory_consults_the_broker(tmp_path, monkeypatch, capsys):
    _init_governed_repo(tmp_path)
    calls = []
    monkeypatch.setattr("pcae.commands.task.observe", lambda **kw: calls.append(kw))
    monkeypatch.chdir(tmp_path)

    main(["doctor", "task-memory"])

    assert len(calls) == 1
    assert calls[0]["requested_capability"] == "pcae_doctor_task_memory"


def test_doctor_task_memory_fix_mode_also_consults_the_broker(tmp_path, monkeypatch, capsys):
    _init_governed_repo(tmp_path)
    calls = []
    monkeypatch.setattr("pcae.commands.task.observe", lambda **kw: calls.append(kw))
    monkeypatch.chdir(tmp_path)

    main(["doctor", "task-memory", "--fix", "--dry-run"])

    assert len(calls) == 1


def test_push_check_consults_the_broker(tmp_path, monkeypatch, capsys):
    _init_governed_repo(tmp_path)
    calls = []
    monkeypatch.setattr("pcae.commands.push.observe", lambda **kw: calls.append(kw))
    monkeypatch.chdir(tmp_path)

    main(["push", "check"])

    assert len(calls) == 1
    assert calls[0]["requested_capability"] == "pcae_push_check"


# ═══════════════════════════════════════════════════════════════════════
# Behavior invariance: decision discarded, output/exit-code unchanged
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("command_args,observe_target", [
    (["check"], "pcae.commands.check.observe"),
    (["doctor", "task-memory"], "pcae.commands.task.observe"),
    (["push", "check"], "pcae.commands.push.observe"),
])
@pytest.mark.parametrize("fake_decision", [DECISION_ALLOW, DECISION_DENY, DECISION_HUMAN_REVIEW])
def test_output_identical_regardless_of_decision(tmp_path, monkeypatch, capsys, command_args, observe_target, fake_decision):
    _init_governed_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(observe_target, lambda **kw: None)
    baseline_exit = main(list(command_args))
    baseline_output = capsys.readouterr().out

    monkeypatch.setattr(observe_target, lambda **kw: _fake_decision(fake_decision))
    variant_exit = main(list(command_args))
    variant_output = capsys.readouterr().out

    assert variant_output == baseline_output
    assert variant_exit == baseline_exit


@pytest.mark.parametrize("command_args,observe_target", [
    (["check"], "pcae.commands.check.observe"),
    (["doctor", "task-memory"], "pcae.commands.task.observe"),
    (["push", "check"], "pcae.commands.push.observe"),
])
def test_output_identical_when_observe_raises(tmp_path, monkeypatch, capsys, command_args, observe_target):
    _init_governed_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(observe_target, lambda **kw: None)
    baseline_exit = main(list(command_args))
    baseline_output = capsys.readouterr().out

    def _raise(**kw):
        raise RuntimeError("simulated observation failure")

    monkeypatch.setattr(observe_target, _raise)
    variant_exit = main(list(command_args))
    variant_output = capsys.readouterr().out

    assert variant_output == baseline_output
    assert variant_exit == baseline_exit


def test_check_json_output_identical_regardless_of_decision(tmp_path, monkeypatch, capsys):
    _init_governed_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr("pcae.commands.check.observe", lambda **kw: None)
    main(["check", "--json"])
    baseline = json.loads(capsys.readouterr().out)

    monkeypatch.setattr("pcae.commands.check.observe", lambda **kw: _fake_decision(DECISION_DENY))
    main(["check", "--json"])
    variant = json.loads(capsys.readouterr().out)

    assert variant == baseline


# ═══════════════════════════════════════════════════════════════════════
# Lifecycle / governance unchanged
# ═══════════════════════════════════════════════════════════════════════


def test_check_scope_enforcement_unaffected_by_observation(tmp_path, monkeypatch, capsys):
    """pcae check's own independent scope/policy logic must still block
    an out-of-scope task exactly as before, regardless of the broker's
    (discarded) decision."""
    _init_governed_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    subprocess.run(
        ["python", "-m", "pcae", "task", "new", "test task",
         "--allowed-file", "README.md"],
        cwd=tmp_path, capture_output=True, text=True, check=True,
    )
    (tmp_path / "NOT_ALLOWED.md").write_text("out of scope\n")

    monkeypatch.setattr("pcae.commands.check.observe", lambda **kw: _fake_decision(DECISION_ALLOW))
    exit_allow = main(["check"])
    out_allow = capsys.readouterr().out

    monkeypatch.setattr("pcae.commands.check.observe", lambda **kw: _fake_decision(DECISION_DENY))
    exit_deny = main(["check"])
    out_deny = capsys.readouterr().out

    assert exit_allow == exit_deny
    assert out_allow == out_deny


def test_push_check_readiness_logic_unaffected_by_observation(tmp_path, monkeypatch, capsys):
    _init_governed_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr("pcae.commands.push.observe", lambda **kw: _fake_decision(DECISION_DENY))
    exit_code = main(["push", "check"])
    output = capsys.readouterr().out

    # Readiness logic (ready/nothing_to_push/blocked) is computed from
    # assess_push_readiness() only -- never from the broker.
    assert "Push readiness check" in output
    assert exit_code in (0, 1)


# ═══════════════════════════════════════════════════════════════════════
# No authorization / no denial / no execution
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("module_name,func_name", [
    ("pcae.commands.check", "run_check"),
    ("pcae.commands.task", "run_doctor_task_memory"),
    ("pcae.commands.push", "run_push_check"),
])
def test_no_authorization_language_in_source(module_name, func_name):
    import importlib
    module = importlib.import_module(module_name)
    source = inspect.getsource(getattr(module, func_name))
    forbidden = ("authorize", "authorization_granted", "execution_authorized", "block_command", "deny_command")
    lowered = source.lower()
    for token in forbidden:
        assert token not in lowered


@pytest.mark.parametrize("module_name,func_name", [
    ("pcae.commands.check", "run_check"),
    ("pcae.commands.task", "run_doctor_task_memory"),
    ("pcae.commands.push", "run_push_check"),
])
def test_broker_result_never_assigned(module_name, func_name):
    import importlib
    module = importlib.import_module(module_name)
    source = inspect.getsource(getattr(module, func_name))
    assert "= observe(" not in source


def test_run_push_never_touched_by_observation():
    """run_push (the real, mutating push command) must not reference
    observe() at all -- only run_push_check does."""
    import pcae.commands.push as push_module
    source = inspect.getsource(push_module.run_push)
    assert "observe(" not in source


# ═══════════════════════════════════════════════════════════════════════
# Compatibility: prior observation path (INT-001, 109B) unchanged
# ═══════════════════════════════════════════════════════════════════════


def test_health_integration_still_present_and_unchanged(tmp_path, monkeypatch, capsys):
    _init_governed_repo(tmp_path)
    calls = []
    monkeypatch.setattr("pcae.commands.health.observe", lambda **kw: calls.append(kw))
    monkeypatch.chdir(tmp_path)

    main(["health"])

    assert len(calls) == 1
    assert calls[0]["requested_capability"] == "pcae_health"


def test_health_tests_still_pass():
    """Direct re-verification that the 109B integration test suite
    (22 tests) still collects and would pass -- run as a subprocess so
    a failure here is unambiguous, not masked by this file's own
    fixtures."""
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/test_permission_broker_command_path_prototype.py", "-q"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0
    assert "22 passed" in result.stdout


# ═══════════════════════════════════════════════════════════════════════
# Broker isolation preserved (permission_broker_foundation untouched)
# ═══════════════════════════════════════════════════════════════════════


def test_broker_foundation_module_still_stdlib_only():
    import ast
    import pcae.core.permission_broker_foundation as pbf
    tree = ast.parse(Path(pbf.__file__).read_text())
    allowed = {"__future__", "uuid", "dataclasses", "datetime"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] in allowed
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                assert node.module.split(".")[0] in allowed


def test_command_path_observation_module_still_isolated():
    import ast
    import pcae.core.command_path_observation as obs_module
    tree = ast.parse(Path(obs_module.__file__).read_text())
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    forbidden = ("subprocess", "shell_gate", "backend_invocations", "notifications")
    for name in names:
        assert not any(f in name for f in forbidden), f"forbidden import: {name}"


# ═══════════════════════════════════════════════════════════════════════
# No execution / no side effects
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("command_args", [
    ["check"], ["doctor", "task-memory"], ["push", "check"],
])
def test_integrated_commands_have_no_extra_side_effects(tmp_path, monkeypatch, capsys, command_args):
    _init_governed_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    before = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if p.is_file())

    main(list(command_args))

    after = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if p.is_file())
    assert before == after
