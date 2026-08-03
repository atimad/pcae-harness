"""Tests for Phase 149F — Repository-Wide Mutation Permission Coverage
Wave 1: source-mutation (AG4 `build_promotion_execution`) integration
with `mutation_permission.evaluate_promotion_permission`.

AG4 is the highest-risk Wave-1 site (can target `src/pcae/**`). These
tests verify: ALLOW required before first file write; DENY/HUMAN_REVIEW/
broker-failure block with zero root mutation; stale decision (candidate/
approved_paths/task changed after ALLOW) blocks with zero root mutation;
divergence-conflict path unaffected; a self-modification target
(`src/pcae/**`) still requires ALLOW but is not specially blocked (per
RWMPC-REQ-019/§9.4 of the 149E plan).
"""

from __future__ import annotations

import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pcae.core import agent as agent_module
from pcae.core import mutation_permission as mp
from pcae.core import permission_broker_foundation as pbf
from pcae.core.paths import HarnessPath
from pcae.core.tasks import create_task_contract


def _init_git_root(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)


def _make_ecp(root, ecp_id="ecp-149f", file_entries=None, git_commit_detected=False):
    entries = file_entries or []
    record = {
        "ecp_id": ecp_id, "ecp_version": "1.0", "prompt_id": "p-149f", "authorization_id": "a",
        "audit_id": "ea", "snapshot_id": "esa-1", "change_record_id": None,
        "execution_result_id": "err-1", "captured_at": "2026-08-03T00:00:00+00:00",
        "capture_source": "sandbox_dir", "capture_outcome": "success", "sandbox_id": "sb-1",
        "sandbox_provider": "git_worktree", "pre_git_head": "abc", "post_git_head": "abc",
        "git_head_diverged": False, "git_commit_detected": git_commit_detected, "manifest_hash": None,
        "file_count": len(entries), "file_entries": entries, "capture_errors": [],
        "binary_file_count": 0, "symlink_count": 0, "external_symlink_count": 0,
        "excluded_file_count": 0, "excluded_paths": [], "absolute_path_writes_detected": False,
        "promotion_eligible_count": sum(1 for e in entries if e.get("promotion_eligible")),
        "esa_available": True, "execution_allowed": False, "promotion_executed": False,
        "rollback_executed": False,
    }
    agent_module.store_execution_change_package(root, record)
    return record


def _make_epr(root, ecp_id, epr_id="epr-149f", approved_paths=None, promotion_authorized=True,
              review_state="approved"):
    record = {
        "epr_id": epr_id, "epr_version": "1.0", "ecp_id": ecp_id, "prompt_id": "p-149f",
        "created_at": "2026-08-03T00:00:00+00:00", "review_state": review_state,
        "human_disposition": review_state,
        "partial_approval": review_state == "partial_approved",
        "approved_paths": approved_paths or [], "rejected_paths": [], "deferred_paths": [],
        "required_modifications": [], "reviewed_by": "human-1",
        "reviewed_at": "2026-08-03T00:00:00+00:00", "review_rationale": None,
        "promotion_authorized": promotion_authorized,
        "override_divergence": False, "override_divergence_rationale": None,
        "execution_allowed": False, "promotion_executed": False,
    }
    agent_module.store_promotion_review(root, record)
    return record


def _entry(path: str, content: str) -> dict:
    return {
        "path": path, "change_type": "added", "before_hash": None,
        "after_hash": hashlib.sha256(content.encode()).hexdigest(),
        "content": content, "binary": False, "promotion_eligible": True,
        "before_content": None, "before_exists": False,
    }


def _setup(tmp_path, entries, approved_paths, with_task=True) -> HarnessPath:
    root_dir = tmp_path / "root"
    root_dir.mkdir()
    _init_git_root(root_dir)
    root = HarnessPath(root_dir)
    if with_task:
        create_task_contract(
            root, "149F promotion integration test task",
            created_at=datetime(2026, 8, 3, 12, 0, tzinfo=timezone.utc),
        )
    ecp = _make_ecp(root, file_entries=entries)
    _make_epr(root, ecp["ecp_id"], approved_paths=approved_paths)
    return root


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


def test_real_allow_writes_file(tmp_path):
    entries = [_entry("docs/new.md", "hello\n")]
    root = _setup(tmp_path, entries, ["docs/new.md"])
    result = agent_module.build_promotion_execution(root, "epr-149f")
    assert result["status"] == "completed"
    assert result["promotion_executed"] is True
    assert (root.path / "docs" / "new.md").read_text() == "hello\n"


# ── DENY / HUMAN_REVIEW / broker failure -> zero root mutation ─────────


@pytest.mark.parametrize("decision", [pbf.DECISION_DENY, pbf.DECISION_HUMAN_REVIEW])
def test_non_allow_decision_blocks_promotion(tmp_path, monkeypatch, decision):
    entries = [_entry("docs/new.md", "hello\n")]
    root = _setup(tmp_path, entries, ["docs/new.md"])
    calls = _force_decision(monkeypatch, decision)

    result = agent_module.build_promotion_execution(root, "epr-149f")
    assert result["error"] == "permission_denied"
    assert result["promoted"] is False
    assert calls["count"] == 1
    assert not (root.path / "docs" / "new.md").exists()


def test_broker_failure_blocks_promotion(tmp_path, monkeypatch):
    entries = [_entry("docs/new.md", "hello\n")]
    root = _setup(tmp_path, entries, ["docs/new.md"])

    def exploding_evaluate(self, request):
        raise RuntimeError("boom")

    monkeypatch.setattr(pbf.PermissionBroker, "evaluate", exploding_evaluate)
    result = agent_module.build_promotion_execution(root, "epr-149f")
    assert result["error"] == "permission_denied"
    assert not (root.path / "docs" / "new.md").exists()


def test_missing_task_denies_promotion(tmp_path):
    entries = [_entry("docs/new.md", "hello\n")]
    root = _setup(tmp_path, entries, ["docs/new.md"], with_task=False)
    result = agent_module.build_promotion_execution(root, "epr-149f")
    assert result["error"] == "permission_denied"
    assert not (root.path / "docs" / "new.md").exists()


# ── divergence-conflict path unaffected (mechanical gate before permission) ──


def test_divergence_conflict_still_blocks_before_permission(tmp_path, monkeypatch):
    entries = [_entry("docs/new.md", "hello\n")]
    root = _setup(tmp_path, entries, ["docs/new.md"])
    calls = {"count": 0}

    def fake_evaluate(self, request):
        calls["count"] += 1
        return pbf.PermissionBrokerDecision(
            decision=pbf.DECISION_ALLOW, decision_reason="x",
            matched_no_go_ids=(), matched_invariants=(), required_remediation=(),
            requires_human=False, simulation_only=True,
        )

    monkeypatch.setattr(pbf.PermissionBroker, "evaluate", fake_evaluate)

    def blocking_divergence(root_arg, ecp, approved_paths):
        return {"blocking": True, "blocking_paths": approved_paths, "file_checks": []}

    monkeypatch.setattr(agent_module, "_pxr_check_divergence", blocking_divergence)
    result = agent_module.build_promotion_execution(root, "epr-149f")
    assert result["error"] == "divergence_conflict"
    # Divergence conflict is a pre-permission mechanical gate -- broker
    # must never be reached for a blocked-divergence attempt.
    assert calls["count"] == 0


# ── stale decision -> zero root mutation ────────────────────────────────


def test_approved_paths_drift_after_allow_blocks_mutation(tmp_path, monkeypatch):
    entries = [_entry("docs/new.md", "hello\n"), _entry("docs/other.md", "other\n")]
    root = _setup(tmp_path, entries, ["docs/new.md"])

    real_evaluate = mp.evaluate_promotion_permission

    def evaluate_then_widen_approved_paths(root_arg, task_id, epr_id, ecp_id, approved_paths):
        result, snapshot = real_evaluate(root_arg, task_id, epr_id, ecp_id, approved_paths)
        # Simulate the EPR's approved_paths widening between decision and
        # first write (e.g. a concurrent re-review).
        store_dir = root_arg.path / agent_module._EPR_STORE_DIR
        epr_path = sorted(store_dir.glob(f"{epr_id}-*.json"), reverse=True)[0]
        import json
        data = json.loads(epr_path.read_text(encoding="utf-8"))
        data["approved_paths"] = ["docs/new.md", "docs/other.md"]
        epr_path.write_text(json.dumps(data), encoding="utf-8")
        return result, snapshot

    monkeypatch.setattr(agent_module.mutation_permission, "evaluate_promotion_permission", evaluate_then_widen_approved_paths)

    result = agent_module.build_promotion_execution(root, "epr-149f")
    assert result["error"] == "permission_decision_stale"
    assert not (root.path / "docs" / "new.md").exists()
    assert not (root.path / "docs" / "other.md").exists()


def test_task_drift_after_allow_blocks_mutation(tmp_path, monkeypatch):
    entries = [_entry("docs/new.md", "hello\n")]
    root = _setup(tmp_path, entries, ["docs/new.md"])

    real_evaluate = mp.evaluate_promotion_permission

    def evaluate_then_change_task(root_arg, task_id, epr_id, ecp_id, approved_paths):
        result, snapshot = real_evaluate(root_arg, task_id, epr_id, ecp_id, approved_paths)
        from pcae.core.tasks import close_active_task_by_identifier

        close_active_task_by_identifier(root_arg, task_id)
        create_task_contract(
            root_arg, "a different task",
            created_at=datetime(2026, 8, 3, 13, 0, tzinfo=timezone.utc),
        )
        return result, snapshot

    monkeypatch.setattr(agent_module.mutation_permission, "evaluate_promotion_permission", evaluate_then_change_task)

    result = agent_module.build_promotion_execution(root, "epr-149f")
    assert result["error"] == "permission_decision_stale"
    assert not (root.path / "docs" / "new.md").exists()


# ── self-modification target requires ALLOW but is not specially blocked ──


def test_src_pcae_target_requires_allow_like_any_other_target(tmp_path, monkeypatch):
    """RWMPC-REQ-019/149E-plan §9.4: no new mechanical hard block exists
    for `src/pcae/**` targets -- the permission boundary applies equally,
    neither more nor less strictly."""
    entries = [_entry("src/pcae/core/example_generated.py", "# generated\n")]
    root = _setup(tmp_path, entries, ["src/pcae/core/example_generated.py"])

    captured = {}
    real_evaluate = mp.evaluate_promotion_permission

    def spy(root_arg, task_id, epr_id, ecp_id, approved_paths):
        result, snapshot = real_evaluate(root_arg, task_id, epr_id, ecp_id, approved_paths)
        captured["action_type"] = result.request.action_type
        return result, snapshot

    monkeypatch.setattr(agent_module.mutation_permission, "evaluate_promotion_permission", spy)

    result = agent_module.build_promotion_execution(root, "epr-149f")
    assert result["status"] == "completed"
    assert captured["action_type"] == pbf.ACTION_SOURCE_MUTATION
    assert (root.path / "src" / "pcae" / "core" / "example_generated.py").exists()


def test_deny_blocks_src_pcae_target_too(tmp_path, monkeypatch):
    entries = [_entry("src/pcae/core/example_generated.py", "# generated\n")]
    root = _setup(tmp_path, entries, ["src/pcae/core/example_generated.py"])
    _force_decision(monkeypatch, pbf.DECISION_DENY)
    result = agent_module.build_promotion_execution(root, "epr-149f")
    assert result["error"] == "permission_denied"
    assert not (root.path / "src" / "pcae").exists()


def test_action_type_classification_prioritizes_src_over_docs():
    assert mp.classify_promotion_action_type(["docs/a.md", "src/x.py"]) == pbf.ACTION_SOURCE_MUTATION
    assert mp.classify_promotion_action_type(["tests/a.py"]) == pbf.ACTION_TEST_MUTATION
    assert mp.classify_promotion_action_type(["docs/a.md"]) == pbf.ACTION_DOCS_MUTATION
    assert mp.classify_promotion_action_type([]) == pbf.ACTION_SOURCE_MUTATION
