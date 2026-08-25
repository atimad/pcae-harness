"""Phase 149O.20L.7O.3F -- Permission Broker Rollback Default-Path
Consumption Integration.

Closes the gap 149O.20L.7O.3E Section 7 identified: `build_rollback_
execution`'s default (non-`HATP_MANDATORY`) dispatch path had zero
Permission Broker coverage at all. This suite verifies the new
`mutation_permission.evaluate_rollback_permission` adapter and its call
site in `build_rollback_execution`, immediately before the file
restore/remove loop, for the default (LEGACY_COMPATIBLE/PREPARED) path
only -- the pre-existing `HATP_MANDATORY` gate is untouched and out of
scope (verified unaffected here too).
"""
from __future__ import annotations

import hashlib
import inspect

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
    return CutoverModeResolution(mode, f"test_fixed_{mode.value}")


def _patch_mode(monkeypatch, mode: CutoverMode) -> None:
    monkeypatch.setattr(
        cutover_mod,
        "resolve_production_hatp_cutover_mode",
        lambda root: _fixed_mode(mode),
    )


def _setup_removable_file_per(tmp_path, *, with_task=True, per_id="per-3f"):
    root_dir = tmp_path / "root"
    root_dir.mkdir()
    # `_init_git_root` (tests/test_agent.py) unconditionally creates an
    # active task contract ("149F test-suite task") as its own Phase 149F
    # precondition-fixture side effect -- remove it for the with_task=False
    # scenario rather than skip `_init_git_root`, so both branches share
    # the exact same git/ECP/PER setup.
    _init_git_root(root_dir)
    (root_dir / "added.txt").write_text("added content")
    root = HarnessPath(root_dir)
    if not with_task:
        import shutil

        active_dir = root_dir / "tasks" / "active"
        if active_dir.is_dir():
            shutil.rmtree(active_dir)
    after_hash = hashlib.sha256(b"added content").hexdigest()
    entries = [{"path": "added.txt", "before_hash": None, "after_hash": after_hash,
                "before_content": None, "before_exists": False, "binary": False}]
    _make_per_test_ecp(root, ecp_id="ecp-3f", file_entries=entries)
    _make_rer_test_per(
        root, per_id=per_id, ecp_id="ecp-3f",
        file_results=[{"path": "added.txt", "outcome": "success"}],
    )
    return root, root_dir


def _force_decision(monkeypatch, decision: str) -> dict:
    calls = {"count": 0}

    def fake_evaluate(self, request):
        calls["count"] += 1
        return pbf.PermissionBrokerDecision(
            decision=decision,
            decision_reason="test_forced",
            matched_no_go_ids=(),
            matched_invariants=(),
            required_remediation=(),
            requires_human=(decision == pbf.DECISION_HUMAN_REVIEW),
            simulation_only=True,
        )

    monkeypatch.setattr(pbf.PermissionBroker, "evaluate", fake_evaluate)
    return calls


# ── real ALLOW positive control ─────────────────────────────────────────


def test_real_allow_permits_default_path_rollback(tmp_path):
    root, root_dir = _setup_removable_file_per(tmp_path)
    result = agent_module.build_rollback_execution(root, "per-3f")
    assert result["status"] == "completed"
    assert result["reverted"] is True
    assert not (root_dir / "added.txt").exists()


@pytest.mark.parametrize("mode", [CutoverMode.LEGACY_COMPATIBLE, CutoverMode.PREPARED])
def test_real_allow_permits_both_default_modes(tmp_path, monkeypatch, mode):
    root, root_dir = _setup_removable_file_per(tmp_path)
    _patch_mode(monkeypatch, mode)
    result = agent_module.build_rollback_execution(root, "per-3f")
    assert result["status"] == "completed"
    assert not (root_dir / "added.txt").exists()


# ── default path invokes broker exactly once, correct identity ─────────


def test_default_path_invokes_broker_with_rollback_action_and_operation_identity(tmp_path, monkeypatch):
    root, _root_dir = _setup_removable_file_per(tmp_path)
    captured = {}
    real_evaluate = mp.evaluate_rollback_permission

    def spy(root_arg, *, task_id, per_id, ecp_id):
        result = real_evaluate(root_arg, task_id=task_id, per_id=per_id, ecp_id=ecp_id)
        captured["action_type"] = result.request.action_type
        captured["execution_class"] = result.request.execution_class
        captured["requested_component"] = result.request.requested_component
        captured["requested_capability"] = result.request.requested_capability
        captured["requested_resource"] = result.request.requested_resource
        captured["task_id"] = task_id
        return result

    monkeypatch.setattr(agent_module.mutation_permission, "evaluate_rollback_permission", spy)
    result = agent_module.build_rollback_execution(root, "per-3f")

    assert result["status"] == "completed"
    assert captured["action_type"] == pbf.ACTION_ROLLBACK
    assert captured["execution_class"] == pbf.EXECUTION_CLASS_MUTATION
    assert captured["requested_component"] == "COMP-008"
    assert captured["requested_capability"] == "build_rollback_execution"
    assert captured["requested_resource"] == "per:per-3f;ecp:ecp-3f"
    assert captured["task_id"] is not None


# ── DENY / broker failure -> zero root mutation ─────────────────────────


def test_deny_blocks_default_path_rollback(tmp_path, monkeypatch):
    root, root_dir = _setup_removable_file_per(tmp_path)
    calls = _force_decision(monkeypatch, pbf.DECISION_DENY)

    result = agent_module.build_rollback_execution(root, "per-3f")
    assert result["error"] == "rollback_permission_denied"
    assert result["reverted"] is False
    assert result["permission_decision"] == pbf.DECISION_DENY
    assert calls["count"] == 1
    assert (root_dir / "added.txt").exists()


def test_broker_failure_blocks_default_path_rollback(tmp_path, monkeypatch):
    root, root_dir = _setup_removable_file_per(tmp_path)

    def exploding_evaluate(self, request):
        raise RuntimeError("boom")

    monkeypatch.setattr(pbf.PermissionBroker, "evaluate", exploding_evaluate)
    result = agent_module.build_rollback_execution(root, "per-3f")
    assert result["error"] == "rollback_permission_denied"
    assert result["permission_decision"] == "BROKER_FAILURE"
    assert (root_dir / "added.txt").exists()


def test_malformed_broker_result_blocks_default_path_rollback(tmp_path, monkeypatch):
    root, root_dir = _setup_removable_file_per(tmp_path)
    monkeypatch.setattr(pbf.PermissionBroker, "evaluate", lambda self, request: None)
    result = agent_module.build_rollback_execution(root, "per-3f")
    assert result["error"] == "rollback_permission_denied"
    assert result["permission_decision"] == "BROKER_FAILURE"
    assert (root_dir / "added.txt").exists()


def test_missing_active_task_denies_default_path_rollback(tmp_path):
    root, root_dir = _setup_removable_file_per(tmp_path, with_task=False)
    result = agent_module.build_rollback_execution(root, "per-3f")
    assert result["error"] == "rollback_permission_denied"
    assert result["permission_reason"] == "missing_active_task_contract"
    assert (root_dir / "added.txt").exists()


def test_human_review_does_not_auto_confirm_default_path_rollback(tmp_path, monkeypatch):
    """`EXECUTION_CLASS_MUTATION` never triggers POL-004 in real production
    code (unlike `EXECUTION_CLASS_ROLLBACK`), so a real HUMAN_REVIEW cannot
    occur on this path today -- but the caller-side handling must still
    treat any non-ALLOW decision, including a forced HUMAN_REVIEW, as
    non-authorized and never translate it into a completed dispatch."""
    root, root_dir = _setup_removable_file_per(tmp_path)
    _force_decision(monkeypatch, pbf.DECISION_HUMAN_REVIEW)
    result = agent_module.build_rollback_execution(root, "per-3f")
    assert result["error"] == "rollback_permission_denied"
    assert result["permission_decision"] == pbf.DECISION_HUMAN_REVIEW
    assert result["reverted"] is False
    assert (root_dir / "added.txt").exists()


def test_execution_class_mutation_never_triggers_pol004_for_rollback():
    """Structural confirmation of the design rationale: POL-004 is scoped
    away from EXECUTION_CLASS_MUTATION, so this adapter cannot itself
    invent a HUMAN_REVIEW requirement."""
    rule = next(
        r for r in pbf.DEFAULT_POLICY_RULES if r.policy_id == "POL-004"
    )
    assert pbf.EXECUTION_CLASS_MUTATION not in rule.applicable_execution_classes
    assert pbf.EXECUTION_CLASS_ROLLBACK in rule.applicable_execution_classes


# ── no silent fallback to the old default path ──────────────────────────


def test_deny_produces_no_partial_file_results(tmp_path, monkeypatch):
    root, _root_dir = _setup_removable_file_per(tmp_path)
    _force_decision(monkeypatch, pbf.DECISION_DENY)
    result = agent_module.build_rollback_execution(root, "per-3f")
    assert result.get("file_results") is None


# ── dry-run unaffected: never reaches the new gate ──────────────────────


def test_dry_run_bypasses_broker_entirely_even_under_forced_deny(tmp_path, monkeypatch):
    root, root_dir = _setup_removable_file_per(tmp_path, with_task=False)
    calls = _force_decision(monkeypatch, pbf.DECISION_DENY)
    result = agent_module.build_rollback_execution(root, "per-3f", dry_run=True)
    assert result["dry_run"] is True
    assert result.get("error") is None
    assert calls["count"] == 0
    assert (root_dir / "added.txt").exists()


# ── HATP_MANDATORY path untouched by the new gate ───────────────────────


def test_hatp_mandatory_path_never_invokes_new_rollback_adapter(tmp_path, monkeypatch):
    root, _root_dir = _setup_removable_file_per(tmp_path, with_task=False)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    calls = {"count": 0}
    real = mp.evaluate_rollback_permission

    def spy(*args, **kwargs):
        calls["count"] += 1
        return real(*args, **kwargs)

    monkeypatch.setattr(agent_module.mutation_permission, "evaluate_rollback_permission", spy)
    result = agent_module.build_rollback_execution(root, "per-3f")
    assert result["error"] == "hatp_evidence_required"
    assert calls["count"] == 0


# ── audit/evidence: denial persists a genuine terminal RER ──────────────


def test_denial_persists_terminal_rer_record(tmp_path, monkeypatch):
    root, _root_dir = _setup_removable_file_per(tmp_path)
    _force_decision(monkeypatch, pbf.DECISION_DENY)
    result = agent_module.build_rollback_execution(root, "per-3f")
    rer_id = result["rer_id"]
    stored = agent_module.lookup_rollback_execution_record(root, rer_id)
    assert stored is not None
    assert stored["status"] == "aborted_permission_denied"
    assert stored["rollback_executed"] is False
    assert "aborted_permission_denied" in agent_module._RER_VALID_STATUSES


# ── idempotency: repeated denied attempts create no duplicate mutation ──


def test_repeated_denied_attempts_stay_zero_mutation(tmp_path, monkeypatch):
    root, root_dir = _setup_removable_file_per(tmp_path)
    _force_decision(monkeypatch, pbf.DECISION_DENY)
    for _ in range(3):
        result = agent_module.build_rollback_execution(root, "per-3f")
        assert result["error"] == "rollback_permission_denied"
    assert (root_dir / "added.txt").exists()
    assert (root_dir / "added.txt").read_text() == "added content"


# ── gate ordering: mechanical divergence-conflict gate still precedes it ──


def test_divergence_conflict_still_blocks_before_permission(tmp_path, monkeypatch):
    root, _root_dir = _setup_removable_file_per(tmp_path)
    calls = {"count": 0}

    def fake_evaluate(self, request):
        calls["count"] += 1
        return pbf.PermissionBrokerDecision(
            decision=pbf.DECISION_ALLOW, decision_reason="x",
            matched_no_go_ids=(), matched_invariants=(), required_remediation=(),
            requires_human=False, simulation_only=True,
        )

    monkeypatch.setattr(pbf.PermissionBroker, "evaluate", fake_evaluate)

    def blocking_divergence(root_arg, ecp, file_plan):
        return {"blocking": True, "blocking_paths": file_plan, "file_checks": []}

    monkeypatch.setattr(agent_module, "_rer_check_divergence", blocking_divergence)
    result = agent_module.build_rollback_execution(root, "per-3f")
    assert result["error"] == "divergence_conflict"
    assert calls["count"] == 0


# ── no bypass: sole production caller, no self-CLI subprocess ──────────


def test_single_production_caller_of_build_rollback_execution():
    import subprocess as _sp
    from pathlib import Path

    src = Path(__file__).resolve().parents[1] / "src" / "pcae"
    result = _sp.run(
        ["grep", "-rn", "build_rollback_execution(", "--include=*.py", str(src)],
        capture_output=True, text=True,
    )
    callers = [
        line for line in result.stdout.splitlines()
        if "def build_rollback_execution" not in line
    ]
    assert callers, "expected at least one production caller"
    assert all("commands/agent.py" in line for line in callers), callers


def test_no_self_cli_subprocess_in_new_adapter_or_gate():
    import ast

    for source in (
        inspect.getsource(mp.evaluate_rollback_permission),
        inspect.getsource(agent_module.build_rollback_execution),
    ):
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = getattr(func, "attr", None) or getattr(func, "id", None)
                if name == "run" or name == "Popen":
                    for arg in node.args:
                        if isinstance(arg, (ast.List, ast.Tuple)) and arg.elts:
                            first = arg.elts[0]
                            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                                assert first.value != "pcae"


def test_gate_placed_before_first_mutation_in_source():
    source = inspect.getsource(agent_module.build_rollback_execution)
    gate_index = source.index("149O.20L.7O.3F")
    first_write_index = min(
        pos for pos in (
            source.find("full_path.write_text"),
            source.find("full_path.write_bytes"),
            source.find("full_path.unlink()"),
        ) if pos != -1
    )
    assert gate_index < first_write_index


# ── readiness/evidence (dry-run) regression: unaffected by this phase ──


def test_dry_run_readiness_unaffected_by_missing_task(tmp_path):
    root, root_dir = _setup_removable_file_per(tmp_path, with_task=False)
    result = agent_module.build_rollback_execution(root, "per-3f", dry_run=True)
    assert result["dry_run"] is True
    assert result.get("error") is None
    assert (root_dir / "added.txt").exists()


# ── cross-consumer distinctness ─────────────────────────────────────────


def test_rollback_operation_identity_distinct_from_promotion_and_publication():
    assert pbf.ACTION_ROLLBACK != pbf.ACTION_SOURCE_MUTATION
    assert pbf.ACTION_ROLLBACK != pbf.ACTION_DOCS_MUTATION
    assert mp._ROLLBACK_CAPABILITY != mp._PUBLICATION_CAPABILITY
    assert mp._ROLLBACK_CAPABILITY != mp._PROMOTION_CAPABILITY
