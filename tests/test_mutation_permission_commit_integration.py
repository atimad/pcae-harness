"""Tests for Phase 149F — Repository-Wide Mutation Permission Coverage
Wave 1: commit-class integration (AG1 `commit_file_changes`, PH1
backend-created-output-adoption commit), sharing
`mutation_permission.evaluate_commit_permission`.

Uses real, local scratch git repositories (no mocked remote mutation) so
at least one commit-class ALLOW path exercises the real, unmodified
Permission Broker Foundation end to end (item 19/49 of the governing
149F instruction), plus targeted negative/staleness coverage.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pcae.commands.init import init_harness
from pcae.core import agent as agent_module
from pcae.core import mutation_permission as mp
from pcae.core import permission_broker_foundation as pbf
from pcae.core.paths import HarnessPath
from pcae.core.tasks import create_task_contract


def _init_repo(tmp_path: Path, with_task: bool = True) -> Path:
    work = tmp_path / "work"
    work.mkdir()
    init_harness(HarnessPath(work))
    subprocess.run(["git", "init"], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=work, check=True, capture_output=True)
    if with_task:
        create_task_contract(
            HarnessPath(work),
            "149F commit integration test task",
            created_at=datetime(2026, 8, 3, 12, 0, tzinfo=timezone.utc),
        )
    subprocess.run(["git", "add", "."], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=work, check=True, capture_output=True)
    return work


def _write_job_and_artifact(root: Path, job_id: str, changed_files: list[str]) -> None:
    jobs_dir = root / ".pcae" / "remote" / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    results_dir = root / ".pcae" / "remote" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    job = {
        "job_id": job_id,
        "requested_agent": "claude-local",
        "change_approval_state": "approved",
    }
    (jobs_dir / f"{job_id}.json").write_text(json.dumps(job), encoding="utf-8")

    artifact = {
        "changed_files": changed_files,
        "scope_validation": {"valid": True, "violations": []},
    }
    (results_dir / f"{job_id}-result.json").write_text(json.dumps(artifact), encoding="utf-8")


def _stage_change(work: Path, filename: str = "impl.py") -> list[str]:
    p = work / filename
    p.write_text("# change\n", encoding="utf-8")
    return [filename]


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


# ── real ALLOW positive control (RWMPC item 19/49) ──────────────────────


def test_real_allow_dispatches_exactly_one_commit(tmp_path, monkeypatch):
    work = _init_repo(tmp_path)
    monkeypatch.chdir(work)
    root = HarnessPath(work)
    changed = _stage_change(work)
    job_id = "job-1"
    _write_job_and_artifact(work, job_id, changed)

    result = agent_module.commit_file_changes(root, job_id)
    assert result["committed"] is True

    log = subprocess.run(
        ["git", "log", "--oneline"], cwd=work, capture_output=True, text=True
    )
    assert len(log.stdout.strip().splitlines()) == 2  # initial + governed commit


# ── DENY / HUMAN_REVIEW / broker failure -> zero commit ────────────────


@pytest.mark.parametrize("decision", [pbf.DECISION_DENY, pbf.DECISION_HUMAN_REVIEW])
def test_non_allow_decision_blocks_commit(tmp_path, monkeypatch, decision):
    work = _init_repo(tmp_path)
    monkeypatch.chdir(work)
    root = HarnessPath(work)
    changed = _stage_change(work)
    job_id = "job-2"
    _write_job_and_artifact(work, job_id, changed)

    calls = _force_decision(monkeypatch, decision)
    before = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=work, capture_output=True, text=True
    ).stdout.strip()

    with pytest.raises(ValueError, match="Permission Broker"):
        agent_module.commit_file_changes(root, job_id)

    assert calls["count"] == 1
    after = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=work, capture_output=True, text=True
    ).stdout.strip()
    assert before == after


def test_broker_failure_blocks_commit(tmp_path, monkeypatch):
    work = _init_repo(tmp_path)
    monkeypatch.chdir(work)
    root = HarnessPath(work)
    changed = _stage_change(work)
    job_id = "job-3"
    _write_job_and_artifact(work, job_id, changed)

    def exploding_evaluate(self, request):
        raise RuntimeError("boom")

    monkeypatch.setattr(pbf.PermissionBroker, "evaluate", exploding_evaluate)

    with pytest.raises(ValueError, match="Permission Broker"):
        agent_module.commit_file_changes(root, job_id)


def test_missing_task_denies_commit(tmp_path):
    """POL-001: missing active task -> DENY -> zero commit."""
    work = _init_repo(tmp_path, with_task=False)
    root = HarnessPath(work)
    changed = _stage_change(work)
    job_id = "job-4"
    _write_job_and_artifact(work, job_id, changed)

    with pytest.raises(ValueError, match="Permission Broker"):
        agent_module.commit_file_changes(root, job_id)


# ── staleness (RWMPC-001 Section 17, item 18/68 of the instruction) ────


def test_staged_content_drift_after_allow_blocks_commit(tmp_path, monkeypatch):
    """ALLOW -> staged content changes before dispatch -> zero commit."""
    work = _init_repo(tmp_path)
    monkeypatch.chdir(work)
    root = HarnessPath(work)
    changed = _stage_change(work)
    job_id = "job-5"
    _write_job_and_artifact(work, job_id, changed)

    real_validate = mp.validate_commit_permission_freshness

    def drifting_validate(root_arg, snapshot):
        # Simulate the index changing between decision and dispatch by
        # mutating the snapshot's staged_tree before the real freshness
        # check runs.
        import dataclasses

        drifted = dataclasses.replace(snapshot, staged_tree="deadbeef" * 5)
        return real_validate(root_arg, drifted)

    monkeypatch.setattr(mp, "validate_commit_permission_freshness", drifting_validate)
    monkeypatch.setattr(agent_module.mutation_permission, "validate_commit_permission_freshness", drifting_validate)

    with pytest.raises(ValueError, match="stale"):
        agent_module.commit_file_changes(root, job_id)


def test_head_drift_after_allow_blocks_commit(tmp_path, monkeypatch):
    """ALLOW -> HEAD changes (another real commit lands) before dispatch
    -> zero commit for the stale attempt."""
    work = _init_repo(tmp_path)
    monkeypatch.chdir(work)
    root = HarnessPath(work)
    changed = _stage_change(work)
    job_id = "job-6"
    _write_job_and_artifact(work, job_id, changed)

    real_evaluate = mp.evaluate_commit_permission

    def evaluate_then_drift_head(root_arg, task_id):
        result, snapshot = real_evaluate(root_arg, task_id)
        # A real, independent commit lands after the decision snapshot
        # was captured, before this attempt dispatches.
        (work / "unrelated.py").write_text("# unrelated\n", encoding="utf-8")
        subprocess.run(["git", "add", "unrelated.py"], cwd=work, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "unrelated"], cwd=work, check=True, capture_output=True
        )
        return result, snapshot

    monkeypatch.setattr(agent_module.mutation_permission, "evaluate_commit_permission", evaluate_then_drift_head)

    with pytest.raises(ValueError, match="stale"):
        agent_module.commit_file_changes(root, job_id)


def test_active_task_drift_after_allow_blocks_commit(tmp_path, monkeypatch):
    work = _init_repo(tmp_path)
    monkeypatch.chdir(work)
    root = HarnessPath(work)
    changed = _stage_change(work)
    job_id = "job-7"
    _write_job_and_artifact(work, job_id, changed)

    real_evaluate = mp.evaluate_commit_permission

    def evaluate_then_change_task(root_arg, task_id):
        result, snapshot = real_evaluate(root_arg, task_id)
        from pcae.core.tasks import close_active_task_by_identifier

        close_active_task_by_identifier(root_arg, task_id)
        create_task_contract(
            root_arg,
            "a different task",
            created_at=datetime(2026, 8, 3, 13, 0, tzinfo=timezone.utc),
        )
        return result, snapshot

    monkeypatch.setattr(agent_module.mutation_permission, "evaluate_commit_permission", evaluate_then_change_task)

    with pytest.raises(ValueError, match="stale"):
        agent_module.commit_file_changes(root, job_id)


def test_commit_message_only_drift_does_not_block(tmp_path, monkeypatch):
    """Commit-message identity is explicitly non-binding (149E plan
    Section 8.2) -- only staged-tree/HEAD/task identity matter."""
    work = _init_repo(tmp_path)
    monkeypatch.chdir(work)
    root = HarnessPath(work)
    changed = _stage_change(work)
    job_id = "job-8"
    _write_job_and_artifact(work, job_id, changed)

    # commit_file_changes derives its own message internally; there is no
    # caller-supplied message to drift. This test documents (rather than
    # forces) that the snapshot does not include a message field at all.
    import dataclasses

    fields = {f.name for f in dataclasses.fields(mp.CommitDecisionSnapshot)}
    assert "message" not in fields
    assert "commit_message" not in fields

    result = agent_module.commit_file_changes(root, job_id)
    assert result["committed"] is True
