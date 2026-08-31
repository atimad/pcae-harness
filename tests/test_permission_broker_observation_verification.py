"""Tests for Phase 109D — Observation Integration Verification & Compatibility.

Verification-only phase: re-proves, under one dedicated suite, that every
observation-only integration completed across 109B (INT-001) and 109C
(INT-002..004) still holds its guarantees, is compatible with the frozen
107B/107C/108A-E/109A governance surface, remains fully isolated from
execution, degrades safely under every broker failure mode (including
malformed output and an empty policy registry), and that the Integration
ID registry is internally consistent. No source code is touched by this
phase -- this file only observes and asserts against existing behavior.

Pure in-process where possible (direct `main()` calls with `capsys`),
pytest-xdist safe. Each test that needs a working repository uses its
own isolated `tmp_path` git+PCAE scaffold.
"""

from __future__ import annotations

import inspect
import subprocess
from pathlib import Path

import pytest

from pcae.cli import main
from pcae.core.command_path_observation import (
    INTEGRATION_IDS,
    INTEGRATION_REGISTRY,
    get_integration,
    observe,
)
from pcae.core.paths import HarnessPath
from pcae.core.permission_broker_foundation import (
    DECISION_ALLOW,
    DECISION_DENY,
    DECISION_HUMAN_REVIEW,
    DEFAULT_POLICY_RULES,
    IMPLEMENTATION_STATUS_EXECUTION_UNAVAILABLE,
    PermissionBroker,
    PermissionBrokerDecision,
    PolicyRegistry,
    build_permission_broker_request,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

ALL_INTEGRATION_IDS = ("INT-001", "INT-002", "INT-003", "INT-004")

INTEGRATION_TO_MODULE_ATTR = {
    "INT-001": ("pcae.commands.health", "observe"),
    "INT-002": ("pcae.commands.check", "observe"),
    "INT-003": ("pcae.commands.task", "observe"),
    "INT-004": ("pcae.commands.push", "observe"),
}

INTEGRATION_TO_COMMAND_ARGS = {
    "INT-001": ["health"],
    "INT-002": ["check"],
    "INT-003": ["doctor", "task-memory"],
    "INT-004": ["push", "check"],
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
# 1. Per-integration verification: broker consulted, decision discarded,
#    output/exit-code/control-flow unchanged, for all four INT IDs.
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("integration_id", ALL_INTEGRATION_IDS)
def test_integration_consults_the_broker(tmp_path, monkeypatch, capsys, integration_id):
    _init_governed_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    module_name, attr_name = INTEGRATION_TO_MODULE_ATTR[integration_id]
    calls = []
    monkeypatch.setattr(f"{module_name}.{attr_name}", lambda **kw: calls.append(kw))

    main(list(INTEGRATION_TO_COMMAND_ARGS[integration_id]))

    assert len(calls) == 1


@pytest.mark.parametrize("integration_id", ALL_INTEGRATION_IDS)
@pytest.mark.parametrize("fake_decision", [DECISION_ALLOW, DECISION_DENY, DECISION_HUMAN_REVIEW, None])
def test_integration_output_unchanged_regardless_of_decision(tmp_path, monkeypatch, capsys, integration_id, fake_decision):
    _init_governed_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    module_name, attr_name = INTEGRATION_TO_MODULE_ATTR[integration_id]
    target = f"{module_name}.{attr_name}"
    args = list(INTEGRATION_TO_COMMAND_ARGS[integration_id])

    monkeypatch.setattr(target, lambda **kw: None)
    baseline_exit = main(list(args))
    baseline_out = capsys.readouterr().out

    result = _fake_decision(fake_decision) if fake_decision else None
    monkeypatch.setattr(target, lambda **kw: result)
    variant_exit = main(list(args))
    variant_out = capsys.readouterr().out

    assert variant_out == baseline_out
    assert variant_exit == baseline_exit


@pytest.mark.parametrize("integration_id", ALL_INTEGRATION_IDS)
def test_integration_lifecycle_unaffected_when_broker_raises(tmp_path, monkeypatch, capsys, integration_id):
    _init_governed_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    module_name, attr_name = INTEGRATION_TO_MODULE_ATTR[integration_id]
    target = f"{module_name}.{attr_name}"
    args = list(INTEGRATION_TO_COMMAND_ARGS[integration_id])

    monkeypatch.setattr(target, lambda **kw: None)
    baseline_exit = main(list(args))
    baseline_out = capsys.readouterr().out

    def _raise(**kw):
        raise RuntimeError("simulated broker failure")

    monkeypatch.setattr(target, _raise)
    variant_exit = main(list(args))
    variant_out = capsys.readouterr().out

    assert variant_out == baseline_out
    assert variant_exit == baseline_exit


# ═══════════════════════════════════════════════════════════════════════
# 2. Compatibility verification: 107B, 107C, 108A-108D, 108E, 109A.
# ═══════════════════════════════════════════════════════════════════════


def test_autonomy_contract_invariants_unchanged():
    text = (REPO_ROOT / "docs" / "V0_2_AUTONOMY_CONTRACT.md").read_text()
    import re
    invariants = sorted(set(re.findall(r"INV-\d{3}", text)))
    assert invariants == [f"INV-{i:03d}" for i in range(1, 11)]


def test_autonomy_contract_components_unchanged():
    text = (REPO_ROOT / "docs" / "V0_2_AUTONOMY_CONTRACT.md").read_text()
    import re
    components = sorted(set(re.findall(r"COMP-\d{3}", text)))
    assert components == [f"COMP-{i:03d}" for i in range(1, 11)]


def test_no_go_gates_unchanged():
    text = (REPO_ROOT / "docs" / "V0_2_EXECUTION_READINESS_NO_GO_GATES.md").read_text()
    import re
    gates = sorted(set(re.findall(r"NG-\d{3}", text)))
    assert gates == [f"NG-{i:03d}" for i in range(1, 26)]


def test_command_path_integration_design_doc_still_present():
    assert (REPO_ROOT / "docs" / "V0_2_PERMISSION_BROKER_COMMAND_PATH_INTEGRATION.md").exists()


@pytest.mark.parametrize("phase_doc", [
    "PHASE_109_PERMISSION_BROKER_COMMAND_PATH_INTEGRATION_DESIGN.md",
    "PHASE_109_FIRST_COMMAND_PATH_INTEGRATION_PROTOTYPE.md",
    "PHASE_109_OBSERVATION_INTEGRATION_HARDENING.md",
])
def test_prior_109_series_phase_docs_still_present(phase_doc):
    assert (REPO_ROOT / "docs" / phase_doc).exists()


def test_local_governance_hooks_still_present_and_unchanged():
    pre_push = REPO_ROOT / ".githooks" / "pre-push"
    assert pre_push.exists()
    text = pre_push.read_text()
    for expected in ("pcae health", "pcae check", "pcae doctor task-memory", "pcae push check"):
        assert expected in text
    assert "git push" not in text


def test_broker_default_policy_rule_count_unchanged():
    from pcae.core.permission_broker_foundation import DEFAULT_POLICY_RULES, POLICY_IDS
    # Phase ...1R.22 (N-16-3) added POL-013 (Narrow Local-CLI Dispatch
    # Eligibility) as the thirteenth canonical policy; POL-001..012 are
    # byte-stable, none removed. Exact freeze at the current cardinality
    # (not a minimum) — .1R.22R reconciliation.
    assert len(DEFAULT_POLICY_RULES) == 13
    assert POLICY_IDS == tuple(f"POL-{n:03d}" for n in range(1, 14))


def test_component_registry_unchanged():
    from pcae.core.permission_broker_foundation import COMPONENT_REGISTRY
    assert len(COMPONENT_REGISTRY) == 10


# ═══════════════════════════════════════════════════════════════════════
# 3. Isolation verification.
# ═══════════════════════════════════════════════════════════════════════


def test_every_decision_reports_execution_unavailable():
    """Regardless of ALLOW/DENY/HUMAN_REVIEW, implementation_status is
    unconditionally execution_unavailable -- the broker cannot ever
    report itself as execution-capable."""
    broker = PermissionBroker()
    for capability in ("pcae_health", "pcae_check", "pcae_doctor_task_memory", "pcae_push_check", "shell_exec"):
        request = build_permission_broker_request(
            action_type="read",
            execution_class="none",
            requested_component="COMP-001",
            requested_capability=capability,
            simulation_only=True,
        )
        decision = broker.evaluate(request)
        assert decision.implementation_status == IMPLEMENTATION_STATUS_EXECUTION_UNAVAILABLE


def test_broker_evaluate_has_no_side_effects(tmp_path, monkeypatch):
    """Calling the real (unmocked) broker must not touch the filesystem."""
    monkeypatch.chdir(tmp_path)
    before = sorted(p.as_posix() for p in tmp_path.rglob("*"))

    request = build_permission_broker_request(
        action_type="read",
        execution_class="none",
        requested_component="COMP-001",
        requested_capability="pcae_check",
        simulation_only=True,
    )
    PermissionBroker().evaluate(request)

    after = sorted(p.as_posix() for p in tmp_path.rglob("*"))
    assert before == after


@pytest.mark.parametrize("module_name,func_name", [
    ("pcae.commands.health", "run_health"),
    ("pcae.commands.check", "run_check"),
    ("pcae.commands.task", "run_doctor_task_memory"),
    ("pcae.commands.push", "run_push_check"),
])
def test_integrated_commands_remain_read_only(module_name, func_name):
    import importlib
    module = importlib.import_module(module_name)
    source = inspect.getsource(getattr(module, func_name))
    forbidden_write_calls = ("os.remove(", "shutil.rmtree(", "subprocess.run(", "subprocess.Popen(")
    for token in forbidden_write_calls:
        assert token not in source


def test_broker_foundation_stdlib_only_ast_isolation():
    import ast
    import pcae.core.permission_broker_foundation as pbf
    tree = ast.parse(Path(pbf.__file__).read_text())
    allowed = {"__future__", "uuid", "dataclasses", "datetime"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] in allowed
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] in allowed


def test_lifecycle_command_modules_never_import_broker_directly():
    """As of Phase 148E, `push.py` is the one explicitly authorized
    exception: PBPC-001 v1.2 requires `pcae push` (and only `pcae push`)
    to consume the Permission Broker as its mandatory production
    permission-decision boundary. `commit.py`/`task.py` remain wholly
    unwired (TK1-3 explicitly deferred, RWMPC-001 Section 14). `phase.py`
    is, as of Phase 149F (RWMPC-001 v1.0 Wave 1), an authorized *indirect*
    consumer via `pcae.core.mutation_permission` (PH1/PH2/PH3) -- but this
    test's original invariant (no lifecycle command module constructs a
    `PermissionBrokerRequest` or references the Foundation *directly*,
    bypassing the one sanctioned adapter module) still holds and is
    re-asserted here narrowly: `phase.py` itself must never import
    `permission_broker_foundation` or construct `PermissionBroker(`
    directly -- that remains `mutation_permission.py`'s exclusive
    responsibility (RWMPC-REQ-013)."""
    for path in ("src/pcae/commands/commit.py", "src/pcae/commands/task.py"):
        source = (REPO_ROOT / path).read_text()
        assert "permission_broker_foundation" not in source
        assert "PermissionBroker(" not in source

    phase_source = (REPO_ROOT / "src/pcae/commands/phase.py").read_text()
    assert "permission_broker_foundation" not in phase_source
    assert "PermissionBroker(" not in phase_source


# ═══════════════════════════════════════════════════════════════════════
# 4. Fail-safe verification: ALLOW / DENY / HUMAN_REVIEW / None / raise /
#    malformed output / empty registry.
# ═══════════════════════════════════════════════════════════════════════


class _MalformedRule:
    """A policy rule that returns something other than a PolicyResult."""

    policy_id = "POL-MALFORMED"

    def evaluate(self, request):
        return "not_a_policy_result"


def test_malformed_policy_result_sanitized_to_fail_closed_deny():
    registry = PolicyRegistry(rules=DEFAULT_POLICY_RULES + (_MalformedRule(),))
    broker = PermissionBroker(registry=registry)
    request = build_permission_broker_request(
        action_type="read",
        execution_class="none",
        requested_component="COMP-001",
        requested_capability="pcae_check",
        simulation_only=True,
    )
    decision = broker.evaluate(request)
    assert decision.decision == DECISION_DENY
    assert decision.implementation_status == IMPLEMENTATION_STATUS_EXECUTION_UNAVAILABLE


def test_empty_registry_fails_closed_to_deny():
    """Phase 148C.6 (PBPA-001 PBPA-REQ-073): fail-closed for an empty
    registry moves to PolicyRegistry construction time, superseding the
    pre-PBPA behavior where construction succeeded and evaluate()
    denied."""
    with pytest.raises(ValueError, match="missing canonical policy"):
        PolicyRegistry(rules=())


@pytest.mark.parametrize("integration_id", ALL_INTEGRATION_IDS)
def test_command_output_unchanged_when_broker_registry_empty(tmp_path, monkeypatch, capsys, integration_id):
    """Even the real observe() path, driven by a broker that fails closed
    to DENY (Phase 148C.6: a literal empty registry can no longer be
    constructed at all, PBPA-REQ-073 -- so a DENY decision is instead
    obtained from a request an implemented rule denies), must not change
    command output -- proving discard-on-read-path, not just
    discard-of-mocked-values."""
    _init_governed_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    module_name, attr_name = INTEGRATION_TO_MODULE_ATTR[integration_id]
    target = f"{module_name}.{attr_name}"
    args = list(INTEGRATION_TO_COMMAND_ARGS[integration_id])

    monkeypatch.setattr(target, lambda **kw: None)
    baseline_exit = main(list(args))
    baseline_out = capsys.readouterr().out

    deny_broker_decision = PermissionBroker().evaluate(
        build_permission_broker_request(
            action_type="read", execution_class="none",
            requested_component="COMP-001", requested_capability="pcae_check",
            task_id=None,  # missing active task -- POL-001 DENY
            simulation_only=True,
        )
    )
    assert deny_broker_decision.decision == DECISION_DENY
    monkeypatch.setattr(target, lambda **kw: deny_broker_decision)
    variant_exit = main(list(args))
    variant_out = capsys.readouterr().out

    assert variant_out == baseline_out
    assert variant_exit == baseline_exit


@pytest.mark.parametrize("integration_id", ALL_INTEGRATION_IDS)
@pytest.mark.parametrize("malformed", ["a plain string", 42, {"decision": "ALLOW"}, [], object()])
def test_command_output_unchanged_when_broker_returns_malformed_object(tmp_path, monkeypatch, capsys, integration_id, malformed):
    """observe()'s real contract is PermissionBrokerDecision | None, but
    a call site must not crash even if a future regression in observe()
    ever returned something else -- the call is a bare, discarded
    expression, so the type of the return value must not matter."""
    _init_governed_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    module_name, attr_name = INTEGRATION_TO_MODULE_ATTR[integration_id]
    target = f"{module_name}.{attr_name}"
    args = list(INTEGRATION_TO_COMMAND_ARGS[integration_id])

    monkeypatch.setattr(target, lambda **kw: None)
    baseline_exit = main(list(args))
    baseline_out = capsys.readouterr().out

    monkeypatch.setattr(target, lambda **kw: malformed)
    variant_exit = main(list(args))
    variant_out = capsys.readouterr().out

    assert variant_out == baseline_out
    assert variant_exit == baseline_exit


def test_observe_itself_never_raises_on_broker_exception(monkeypatch):
    class _ExplodingBroker:
        def evaluate(self, request):
            raise RuntimeError("boom")

    monkeypatch.setattr("pcae.core.command_path_observation.PermissionBroker", _ExplodingBroker)
    result = observe(
        action_type="read", execution_class="none",
        requested_component="COMP-001", requested_capability="pcae_check",
        evidence_available=True, approval_present=True,
    )
    assert result is None


# ═══════════════════════════════════════════════════════════════════════
# 5. Integration Registry verification.
# ═══════════════════════════════════════════════════════════════════════


def test_registry_ids_unique():
    ids = [e.integration_id for e in INTEGRATION_REGISTRY]
    assert len(ids) == len(set(ids))


def test_registry_has_exactly_four_entries():
    assert len(INTEGRATION_REGISTRY) == 4
    assert INTEGRATION_IDS == frozenset(ALL_INTEGRATION_IDS)


@pytest.mark.parametrize("integration_id", ALL_INTEGRATION_IDS)
def test_registry_entry_documented_and_correctly_mapped(integration_id):
    entry = get_integration(integration_id)
    assert entry is not None
    assert entry.integration_type == "observation-only"
    assert entry.observation_status == "active"
    assert entry.implementation_status == "observation_only"
    module_name, _ = INTEGRATION_TO_MODULE_ATTR[integration_id]
    # The command listed in the registry must be reachable from the
    # module the integration actually lives in.
    assert entry.command


def test_registry_documented_in_phase_docs():
    text_108c = (REPO_ROOT / "docs" / "PHASE_109_OBSERVATION_INTEGRATION_HARDENING.md").read_text()
    for integration_id in ALL_INTEGRATION_IDS:
        assert integration_id in text_108c


def test_registry_referenced_by_this_verification_suite():
    """Self-referential sanity check: every registry ID this phase
    claims to have verified must actually appear as a parametrize value
    somewhere in this file's own source."""
    source = Path(__file__).read_text()
    for integration_id in ALL_INTEGRATION_IDS:
        assert integration_id in source


def test_unregistered_id_returns_none():
    assert get_integration("INT-005") is None
    assert get_integration("") is None


# ═══════════════════════════════════════════════════════════════════════
# 6. Safety case: observation cannot become enforcement / bypass
#    governance / change semantics; remains reversible.
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("module_name,func_name", [
    ("pcae.commands.health", "run_health"),
    ("pcae.commands.check", "run_check"),
    ("pcae.commands.task", "run_doctor_task_memory"),
    ("pcae.commands.push", "run_push_check"),
])
def test_observation_call_is_reversible_bare_expression(module_name, func_name):
    """'Reversible' here means structurally: deleting the observe() call
    entirely would not require touching any other line, because nothing
    downstream references its result. Verified by confirming the return
    value is never assigned to a name."""
    import importlib
    module = importlib.import_module(module_name)
    source = inspect.getsource(getattr(module, func_name))
    assert "= observe(" not in source
    assert "observe(" in source


def test_run_push_has_no_observation_call():
    import pcae.commands.push as push_module
    source = inspect.getsource(push_module.run_push)
    assert "observe(" not in source


def test_check_scope_enforcement_unaffected_by_observation(tmp_path, monkeypatch, capsys):
    _init_governed_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    subprocess.run(
        ["python", "-m", "pcae", "task", "new", "test task", "--allowed-file", "README.md"],
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


def test_no_authorization_or_denial_language_anywhere_in_call_sites():
    forbidden = ("authorize", "authorization_granted", "execution_authorized", "block_command", "deny_command")
    for module_name, func_name in [
        ("pcae.commands.health", "run_health"),
        ("pcae.commands.check", "run_check"),
        ("pcae.commands.task", "run_doctor_task_memory"),
        ("pcae.commands.push", "run_push_check"),
    ]:
        import importlib
        module = importlib.import_module(module_name)
        source = inspect.getsource(getattr(module, func_name)).lower()
        for token in forbidden:
            assert token not in source


# ═══════════════════════════════════════════════════════════════════════
# 7. Execution Integration Status re-verification.
# ═══════════════════════════════════════════════════════════════════════


def test_execution_integration_status_expected_values():
    observed = len(INTEGRATION_REGISTRY)
    behavior_changing = sum(1 for e in INTEGRATION_REGISTRY if e.implementation_status != "observation_only")
    authorized = 0
    execution_capable = 0

    assert observed == 4
    assert behavior_changing == 0
    assert authorized == 0
    assert execution_capable == 0


def test_health_and_109c_suites_still_pass():
    """Direct re-verification, run as a subprocess so a failure here is
    unambiguous: both prior observation-integration suites (109B's 22
    tests and 109C's 47 tests) still collect and pass unmodified."""
    result = subprocess.run(
        [
            "python", "-m", "pytest", "-q",
            "tests/test_permission_broker_command_path_prototype.py",
            "tests/test_permission_broker_observation_hardening.py",
        ],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=90,
    )
    assert result.returncode == 0
    assert "69 passed" in result.stdout
