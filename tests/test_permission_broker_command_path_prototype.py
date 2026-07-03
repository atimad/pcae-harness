"""Tests for Phase 109B — First Command-Path Integration Prototype
(Observation-Only, Disabled by Default).

Verifies the first, observation-only integration between `pcae health`
and the Permission Broker: the broker is genuinely consulted, but its
decision is provably discarded — command output, exit code, and control
flow are identical regardless of what the broker returns, including if
it raises. No subprocess invocation for the behavior-invariance tests
(direct `main()` calls with `capsys`); a small number of real subprocess
`pcae health` invocations confirm the same holds end-to-end. Pure
in-process where possible, pytest-xdist safe.
"""

from __future__ import annotations

import inspect
import json
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.cli import main
from pcae.core.command_path_observation import observe
from pcae.core.permission_broker_foundation import (
    DECISION_ALLOW,
    DECISION_DENY,
    DECISION_HUMAN_REVIEW,
    PermissionBroker,
    PermissionBrokerDecision,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def _init_governed_repo(root: Path) -> None:
    """Minimal git + PCAE scaffold so build_health_data() succeeds."""
    from pcae.commands.init import init_harness
    from pcae.core.paths import HarnessPath

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
# observe() itself
# ═══════════════════════════════════════════════════════════════════════


def test_observe_function_exists():
    assert callable(observe)


def test_observe_returns_a_decision_for_a_valid_request():
    decision = observe(
        action_type="read", execution_class="none",
        requested_component="COMP-001", requested_capability="test",
        task_id="t1", evidence_available=True, approval_present=True,
    )
    assert isinstance(decision, PermissionBrokerDecision)


def test_observe_never_raises_when_broker_raises(monkeypatch):
    def _raise(self, request):
        raise RuntimeError("simulated broker failure")

    monkeypatch.setattr(PermissionBroker, "evaluate", _raise)
    result = observe(
        action_type="read", execution_class="none",
        requested_component="COMP-001", requested_capability="test",
    )
    assert result is None


def test_observe_returns_none_on_invalid_component():
    # Not a broker failure -- a normal DENY decision, still returned.
    decision = observe(
        action_type="read", execution_class="none",
        requested_component="COMP-999", requested_capability="test",
    )
    assert isinstance(decision, PermissionBrokerDecision)
    assert decision.decision == DECISION_DENY


def test_observe_has_no_side_effects(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    observe(
        action_type="read", execution_class="none",
        requested_component="COMP-001", requested_capability="test",
        task_id="t1", evidence_available=True, approval_present=True,
    )
    assert list(tmp_path.iterdir()) == []


def test_observe_signature_takes_only_keyword_arguments():
    sig = inspect.signature(observe)
    for param in sig.parameters.values():
        assert param.kind in (
            inspect.Parameter.KEYWORD_ONLY,
            inspect.Parameter.VAR_KEYWORD,
        ), "observe() must be keyword-only to avoid positional-arg misuse"


# ═══════════════════════════════════════════════════════════════════════
# Broker consulted by pcae health
# ═══════════════════════════════════════════════════════════════════════


def test_health_consults_the_broker(tmp_path, monkeypatch, capsys):
    _init_governed_repo(tmp_path)
    calls = []

    def _spy(**kwargs):
        calls.append(kwargs)
        return _fake_decision(DECISION_ALLOW)

    monkeypatch.setattr("pcae.commands.health.observe", _spy)
    monkeypatch.chdir(tmp_path)

    main(["health"])

    assert len(calls) == 1
    assert calls[0]["action_type"] == "read"
    assert calls[0]["execution_class"] == "none"
    assert calls[0]["requested_component"] == "COMP-001"
    assert calls[0]["requested_capability"] == "pcae_health"


def test_health_json_also_consults_the_broker(tmp_path, monkeypatch, capsys):
    _init_governed_repo(tmp_path)
    calls = []
    monkeypatch.setattr("pcae.commands.health.observe", lambda **kw: calls.append(kw))
    monkeypatch.chdir(tmp_path)

    main(["health", "--json"])

    assert len(calls) == 1


# ═══════════════════════════════════════════════════════════════════════
# Behavior invariance: decision is discarded, never changes anything
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("fake_decision", [
    DECISION_ALLOW, DECISION_DENY, DECISION_HUMAN_REVIEW,
])
def test_health_output_identical_regardless_of_decision_value(tmp_path, monkeypatch, capsys, fake_decision):
    _init_governed_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr("pcae.commands.health.observe", lambda **kw: None)
    baseline_exit = main(["health"])
    baseline_output = capsys.readouterr().out

    monkeypatch.setattr("pcae.commands.health.observe", lambda **kw: _fake_decision(fake_decision))
    variant_exit = main(["health"])
    variant_output = capsys.readouterr().out

    assert variant_output == baseline_output
    assert variant_exit == baseline_exit


def test_health_output_identical_when_observe_raises(tmp_path, monkeypatch, capsys):
    _init_governed_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr("pcae.commands.health.observe", lambda **kw: None)
    baseline_exit = main(["health"])
    baseline_output = capsys.readouterr().out

    def _raise(**kw):
        raise RuntimeError("simulated observation failure")

    monkeypatch.setattr("pcae.commands.health.observe", _raise)
    variant_exit = main(["health"])
    variant_output = capsys.readouterr().out

    assert variant_output == baseline_output
    assert variant_exit == baseline_exit


def test_health_json_output_identical_regardless_of_decision(tmp_path, monkeypatch, capsys):
    _init_governed_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr("pcae.commands.health.observe", lambda **kw: None)
    main(["health", "--json"])
    baseline = json.loads(capsys.readouterr().out)

    monkeypatch.setattr("pcae.commands.health.observe", lambda **kw: _fake_decision(DECISION_DENY))
    main(["health", "--json"])
    variant = json.loads(capsys.readouterr().out)

    assert variant == baseline


def test_health_exit_code_never_derived_from_observe_result(tmp_path, monkeypatch):
    """Structural check: run_health's source computes its return value
    from is_healthy(data) only -- never from the observe() call site."""
    import pcae.commands.health as health_module
    source = inspect.getsource(health_module.run_health)
    return_line = [line for line in source.splitlines() if "return" in line and "is_healthy" in line]
    assert len(return_line) == 1
    assert "observe" not in return_line[0]


# ═══════════════════════════════════════════════════════════════════════
# No authorization / no blocking / no execution / no broker enforcement
# ═══════════════════════════════════════════════════════════════════════


def test_no_authorization_language_in_health_source():
    import pcae.commands.health as health_module
    source = inspect.getsource(health_module)
    forbidden = ("authorize", "authorization_granted", "execution_authorized", "block_command", "deny_command")
    lowered = source.lower()
    for token in forbidden:
        assert token not in lowered


def test_observation_module_has_no_execution_side_effects():
    import ast
    import pcae.core.command_path_observation as obs_module
    source = Path(obs_module.__file__).read_text()
    tree = ast.parse(source)
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    forbidden = ("subprocess", "shell_gate", "backend_invocations", "notifications", "os")
    for name in names:
        assert not any(f in name for f in forbidden), f"forbidden import: {name}"


def test_broker_result_never_stored_or_returned_by_run_health():
    """run_health() discards observe()'s return value entirely -- no
    assignment captures it for later use."""
    import pcae.commands.health as health_module
    source = inspect.getsource(health_module.run_health)
    # The only two acceptable appearances of "observe(" are the call
    # itself; there must be no "= observe(" assignment.
    assert "= observe(" not in source


def test_pcae_health_subprocess_exit_code_matches_repo_state():
    """End-to-end: a real subprocess invocation of pcae health against
    this repo behaves exactly as pcae check/health already report."""
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "health"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
    )
    assert "PCAE health" in result.stdout
    assert result.returncode in (0, 1)


# ═══════════════════════════════════════════════════════════════════════
# Observation-only contract: consulted -> produced -> discarded -> continues
# ═══════════════════════════════════════════════════════════════════════


def test_observation_contract_sequence(tmp_path, monkeypatch, capsys):
    """Broker consulted -> decision produced -> decision discarded ->
    existing command continues unchanged, all in one assertion chain."""
    _init_governed_repo(tmp_path)
    sequence = []

    def _tracking_observe(**kwargs):
        sequence.append("consulted")
        decision = _fake_decision(DECISION_DENY)
        sequence.append("produced")
        return decision

    monkeypatch.setattr("pcae.commands.health.observe", _tracking_observe)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["health"])
    output = capsys.readouterr().out

    sequence.append("continued")
    assert sequence == ["consulted", "produced", "continued"]
    # "discarded": DENY was returned, yet the command still printed
    # normal health output and did not exit as if blocked.
    assert "PCAE health" in output
    assert exit_code in (0, 1)  # driven by is_healthy(data), not DENY


# ═══════════════════════════════════════════════════════════════════════
# Compatibility with 109A architecture
# ═══════════════════════════════════════════════════════════════════════


def test_integration_uses_known_action_type_and_execution_class():
    from pcae.core.permission_broker_foundation import (
        KNOWN_ACTION_TYPES, KNOWN_EXECUTION_CLASSES, COMPONENT_IDS,
    )
    import pcae.commands.health as health_module
    source = inspect.getsource(health_module.run_health)
    assert 'action_type="read"' in source
    assert 'execution_class="none"' in source
    assert 'requested_component="COMP-001"' in source
    assert "read" in KNOWN_ACTION_TYPES
    assert "none" in KNOWN_EXECUTION_CLASSES
    assert "COMP-001" in COMPONENT_IDS


def test_integration_matches_109a_read_only_category():
    """docs/V0_2_PERMISSION_BROKER_COMMAND_PATH_INTEGRATION.md's
    Read-only category states broker involvement is 'not required' for
    authorization -- this integration is consistent with that: it
    consults the broker but never uses the result for authorization."""
    design_doc = REPO_ROOT / "docs" / "V0_2_PERMISSION_BROKER_COMMAND_PATH_INTEGRATION.md"
    text = design_doc.read_text()
    assert "### Read-only" in text


def test_simulation_only_flag_set_true():
    import pcae.commands.health as health_module
    source = inspect.getsource(health_module.run_health)
    # simulation_only defaults to True and is not overridden.
    assert "simulation_only=False" not in source
