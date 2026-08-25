"""Phase 149O.20L.7O.3F.1 -- Independent End-to-End Rollback
Permission-Boundary Verification.

Independently re-derives (does not import or trust) the claims made by
Phase 149O.20L.7O.3F's own test suite
(`tests/test_phase_149o_20l_7o_3f_rollback_permission_broker_default_path.py`).
This suite only reuses the pre-existing shared fixture helpers from
`tests/test_agent.py` (`_init_git_root`, `_make_per_test_ecp`,
`_make_rer_test_per`) -- ordinary disposable-repo test scaffolding used
throughout this test file, not 3F-specific evidence -- and writes its
own independent assertions and scenarios against current source.
"""
from __future__ import annotations

import hashlib

import pytest

from pcae.core import agent as agent_module
from pcae.core import hatp_mandatory_cutover as cutover_mod
from pcae.core import mutation_permission as mp
from pcae.core import permission_broker_foundation as pbf
from pcae.core.hatp_mandatory_cutover import CutoverMode, CutoverModeResolution
from pcae.core.paths import HarnessPath

from tests.test_agent import _init_git_root, _make_per_test_ecp, _make_rer_test_per

pytestmark = pytest.mark.fast_green


def _fixed_mode(mode: CutoverMode) -> CutoverModeResolution:
    return CutoverModeResolution(mode, "verification_fixed_mode")


def _patch_mode(monkeypatch, mode: CutoverMode) -> None:
    monkeypatch.setattr(
        cutover_mod, "resolve_production_hatp_cutover_mode", lambda root: _fixed_mode(mode),
    )


def _disposable_root(tmp_path, *, per_id="per-v"):
    """Fresh disposable git root with one removable-file PER, ready for a
    real (non-dry-run) default-path rollback attempt."""
    root_dir = tmp_path / "root"
    root_dir.mkdir()
    _init_git_root(root_dir)
    (root_dir / "added.txt").write_text("independent-verification content")
    root = HarnessPath(root_dir)
    after_hash = hashlib.sha256(b"independent-verification content").hexdigest()
    entries = [{
        "path": "added.txt", "before_hash": None, "after_hash": after_hash,
        "before_content": None, "before_exists": False, "binary": False,
    }]
    _make_per_test_ecp(root, ecp_id="ecp-v", file_entries=entries)
    _make_rer_test_per(
        root, per_id=per_id, ecp_id="ecp-v",
        file_results=[{"path": "added.txt", "outcome": "success"}],
    )
    return root, root_dir


# ── (a) direct-helper reachability: no bypass around build_rollback_execution ──

def test_no_other_production_caller_of_build_rollback_execution():
    """Item 4: `build_rollback_execution` must have exactly one production
    caller (the CLI command handler) -- any second caller would be a
    potential bypass of the new gate."""
    import subprocess
    out = subprocess.run(
        ["grep", "-rn", r"build_rollback_execution(", "src/pcae"],
        cwd=agent_module.__file__.rsplit("/src/", 1)[0], capture_output=True, text=True,
    )
    call_sites = [
        line for line in out.stdout.splitlines()
        if "def build_rollback_execution" not in line and "build_rollback_execution(" in line
    ]
    non_test_callers = [line for line in call_sites if "/commands/agent.py" in line]
    assert len(call_sites) == 1, f"unexpected caller count: {call_sites}"
    assert len(non_test_callers) == 1


def test_direct_helper_invocation_still_gated_and_denied(tmp_path, monkeypatch):
    """Calling `build_rollback_execution` directly (bypassing any CLI
    wrapper) with a broker-forced DENY must still block the effect --
    proves the gate is not merely a CLI-level check."""
    root, root_dir = _disposable_root(tmp_path)

    def fake_evaluate(self, request):
        return pbf.PermissionBrokerDecision(
            decision=pbf.DECISION_DENY, decision_reason="verification_deny",
            matched_no_go_ids=(), matched_invariants=(), required_remediation=(),
            requires_human=False, simulation_only=True,
        )

    monkeypatch.setattr(pbf.PermissionBroker, "evaluate", fake_evaluate)
    result = agent_module.build_rollback_execution(root, "per-v")
    assert result["execution_allowed"] is False
    assert result["error"] == "rollback_permission_denied"
    # fixture pre-creates added.txt on disk; the rollback plan would
    # *remove* it (before_exists=False) -- DENY must leave it untouched.
    assert (root_dir / "added.txt").exists() is True
    assert not result["reverted"]


# ── (b) ALLOW end-to-end ────────────────────────────────────────────────

def test_allow_end_to_end_permits_preexisting_dispatch_behavior(tmp_path):
    root, root_dir = _disposable_root(tmp_path)
    result = agent_module.build_rollback_execution(root, "per-v")
    assert result["status"] == "completed"
    assert result["reverted"] is True
    assert not (root_dir / "added.txt").exists()


# ── (c) DENY end-to-end: zero mutation, correct terminal status ────────

def test_deny_end_to_end_zero_mutation_and_terminal_status(tmp_path, monkeypatch):
    root, root_dir = _disposable_root(tmp_path)
    monkeypatch.setattr(
        pbf.PermissionBroker, "evaluate",
        lambda self, request: pbf.PermissionBrokerDecision(
            decision=pbf.DECISION_DENY, decision_reason="verification_deny",
            matched_no_go_ids=(), matched_invariants=(), required_remediation=(),
            requires_human=False, simulation_only=True,
        ),
    )
    result = agent_module.build_rollback_execution(root, "per-v")
    assert result["error"] == "rollback_permission_denied"
    assert result["reverted"] is False
    assert (root_dir / "added.txt").exists()  # unlink never attempted

    stored = agent_module.lookup_rollback_execution_record(root, result["rer_id"])
    assert stored["status"] == "aborted_permission_denied"
    assert stored["rollback_executed"] is False
    assert stored["file_results"] == []  # no file_results appended -- loop never entered


# ── (d) broker exception -> fail-closed ─────────────────────────────────

def test_broker_exception_fails_closed(tmp_path, monkeypatch):
    root, root_dir = _disposable_root(tmp_path)

    def boom(self, request):
        raise RuntimeError("simulated broker crash")

    monkeypatch.setattr(pbf.PermissionBroker, "evaluate", boom)
    result = agent_module.build_rollback_execution(root, "per-v")
    assert result["execution_allowed"] is False
    assert result["error"] == "rollback_permission_denied"
    assert (root_dir / "added.txt").exists()


# ── (e) malformed broker result cannot be treated as ALLOW ─────────────

def test_malformed_broker_result_not_treated_as_allow(tmp_path, monkeypatch):
    root, root_dir = _disposable_root(tmp_path)
    monkeypatch.setattr(pbf.PermissionBroker, "evaluate", lambda self, request: "ALLOW")
    result = agent_module.build_rollback_execution(root, "per-v")
    assert result["execution_allowed"] is False
    assert result["error"] == "rollback_permission_denied"
    assert (root_dir / "added.txt").exists()


def test_evaluate_repository_mutation_permission_rejects_non_decision_object():
    """Unit-level: the shared primitive itself, independent of the
    rollback call site, must not treat a truthy non-decision object as
    authorized."""
    class FakeBroker:
        def evaluate(self, request):
            return object()  # not a PermissionBrokerDecision

    result = mp.evaluate_repository_mutation_permission(
        root=HarnessPath("."), action_type=pbf.ACTION_ROLLBACK,
        execution_class=pbf.EXECUTION_CLASS_MUTATION, requested_component="COMP-008",
        requested_capability="build_rollback_execution", task_id=None,
        requested_resource=None, evidence_available=True, approval_present=False,
        simulation_only=True, broker=FakeBroker(),
    )
    assert result.authorized is False
    assert result.broker_failure_reason == "invalid_broker_result"


# ── (f) dry-run never invokes the broker ────────────────────────────────

def test_dry_run_never_invokes_broker(tmp_path, monkeypatch):
    root, root_dir = _disposable_root(tmp_path)
    calls = {"n": 0}
    real = mp.evaluate_rollback_permission

    def spy(*args, **kwargs):
        calls["n"] += 1
        return real(*args, **kwargs)

    monkeypatch.setattr(mp, "evaluate_rollback_permission", spy)
    monkeypatch.setattr(agent_module, "mutation_permission", mp)
    result = agent_module.build_rollback_execution(root, "per-v", dry_run=True)
    assert result["dry_run"] is True
    assert calls["n"] == 0
    assert (root_dir / "added.txt").exists()  # dry run touches nothing


# ── (g) HATP_MANDATORY path does not invoke the new adapter ────────────

def test_hatp_mandatory_mode_never_invokes_new_adapter(tmp_path, monkeypatch):
    root, _root_dir = _disposable_root(tmp_path)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    calls = {"n": 0}
    real = mp.evaluate_rollback_permission

    def spy(*args, **kwargs):
        calls["n"] += 1
        return real(*args, **kwargs)

    monkeypatch.setattr(mp, "evaluate_rollback_permission", spy)
    monkeypatch.setattr(agent_module, "mutation_permission", mp)
    result = agent_module.build_rollback_execution(root, "per-v")  # no hatp_evidence_id
    assert result["error"] == "hatp_evidence_required"
    assert calls["n"] == 0


@pytest.mark.parametrize("mode", [CutoverMode.LEGACY_COMPATIBLE, CutoverMode.PREPARED])
def test_default_modes_do_invoke_new_adapter(tmp_path, monkeypatch, mode):
    root, _root_dir = _disposable_root(tmp_path)
    _patch_mode(monkeypatch, mode)
    calls = {"n": 0}
    real = mp.evaluate_rollback_permission

    def spy(*args, **kwargs):
        calls["n"] += 1
        return real(*args, **kwargs)

    monkeypatch.setattr(mp, "evaluate_rollback_permission", spy)
    monkeypatch.setattr(agent_module, "mutation_permission", mp)
    result = agent_module.build_rollback_execution(root, "per-v")
    assert calls["n"] == 1
    assert result["status"] == "completed"


# ── (h) runtime capability unaffected by an ALLOW rollback ─────────────

def test_runtime_capability_unchanged_after_allow(tmp_path):
    import json
    import subprocess

    root, _root_dir = _disposable_root(tmp_path)

    def _inspect():
        out = subprocess.run(
            ["pcae", "runtime", "inspect", "--json"], cwd=root.path,
            capture_output=True, text=True, check=True,
        )
        return json.loads(out.stdout)

    before = _inspect()
    agent_module.build_rollback_execution(root, "per-v")
    after = _inspect()
    assert before["health"]["current_runtime_state"] == after["health"]["current_runtime_state"] == "Observed"
    assert before["health"]["execution_availability"] == after["health"]["execution_availability"] == "unavailable"
    assert before["health"]["current_maximum_plugin_capability"] == after["health"]["current_maximum_plugin_capability"] == "observe"


# ── (i) DENY retry: deterministic, no duplicate/inconsistent record ─────

def test_deny_retry_is_deterministic(tmp_path, monkeypatch):
    root, root_dir = _disposable_root(tmp_path)
    monkeypatch.setattr(
        pbf.PermissionBroker, "evaluate",
        lambda self, request: pbf.PermissionBrokerDecision(
            decision=pbf.DECISION_DENY, decision_reason="verification_deny",
            matched_no_go_ids=(), matched_invariants=(), required_remediation=(),
            requires_human=False, simulation_only=True,
        ),
    )
    first = agent_module.build_rollback_execution(root, "per-v")
    second = agent_module.build_rollback_execution(root, "per-v")
    assert first["rer_id"] != second["rer_id"]  # each dispatch attempt gets its own RER
    assert first["error"] == second["error"] == "rollback_permission_denied"
    assert (root_dir / "added.txt").exists()


# ── (j) operation identity: correct, distinct binding ───────────────────

def test_operation_identity_correct_and_distinct_from_push(tmp_path, monkeypatch):
    root, _root_dir = _disposable_root(tmp_path)
    captured = {}
    real_evaluate = pbf.PermissionBroker.evaluate

    def spy(self, request):
        captured["request"] = request
        return real_evaluate(self, request)

    monkeypatch.setattr(pbf.PermissionBroker, "evaluate", spy)
    agent_module.build_rollback_execution(root, "per-v")
    req = captured["request"]
    assert req.action_type == pbf.ACTION_ROLLBACK
    assert req.execution_class == pbf.EXECUTION_CLASS_MUTATION
    assert req.requested_component == "COMP-008"
    assert req.requested_capability == "build_rollback_execution"
    assert req.action_type != pbf.ACTION_PUSH
    assert req.requested_component != mp._PUSH_COMPONENT


# ── policy-registry re-derivation (independent of 3F's own docstring claims) ──

def test_pol004_excludes_execution_class_mutation():
    rule = next(r for r in pbf.DEFAULT_POLICY_RULES if r.policy_id == "POL-004")
    assert pbf.EXECUTION_CLASS_MUTATION not in rule.applicable_execution_classes
    assert pbf.EXECUTION_CLASS_ROLLBACK in rule.applicable_execution_classes


def test_comp008_registered_generically_not_hatp_specific():
    entry = next(
        c for c in pbf.COMPONENT_REGISTRY if c.component_id == "COMP-008"
    )
    assert entry.name == "Rollback Boundary"


def test_rollback_adapter_reuses_same_primitive_as_commit_and_push():
    import inspect
    src = inspect.getsource(mp.evaluate_rollback_permission)
    assert "evaluate_repository_mutation_permission" in src
    commit_src = inspect.getsource(mp.evaluate_commit_permission)
    assert "evaluate_repository_mutation_permission" in commit_src


# ── aborted_permission_denied: safe, minimal consumer footprint ─────────

def test_aborted_permission_denied_not_flagged_as_interrupted_or_partial(tmp_path, monkeypatch):
    """A terminal aborted_permission_denied record must not be picked up
    by reconciliation logic that watches for in_progress/partial RERs."""
    root, _root_dir = _disposable_root(tmp_path)
    monkeypatch.setattr(
        pbf.PermissionBroker, "evaluate",
        lambda self, request: pbf.PermissionBrokerDecision(
            decision=pbf.DECISION_DENY, decision_reason="verification_deny",
            matched_no_go_ids=(), matched_invariants=(), required_remediation=(),
            requires_human=False, simulation_only=True,
        ),
    )
    result = agent_module.build_rollback_execution(root, "per-v")
    rer = agent_module.lookup_rollback_execution_record(root, result["rer_id"])
    issues = agent_module._ect_check_interrupted_states([], [rer])
    issues += agent_module._ect_check_partial_states([], [rer])
    assert issues == []


def test_aborted_permission_denied_is_a_recognized_valid_status():
    assert "aborted_permission_denied" in agent_module._RER_VALID_STATUSES
