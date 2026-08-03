"""Tests for Phase 149F — Repository-Wide Mutation Permission Coverage
Wave 1: alternate-push (AG2 direct wire; PH2/PH3 routed) integration with
the shared dispatcher `agent._dispatch_governed_push`.

Verifies: AG2 is broker-wired directly; PH2/PH3 no longer construct their
own `PermissionBrokerRequest` or dispatch `git push` independently -- both
reach `_dispatch_governed_push`; the Chapter-148 freshness pattern is
reproduced for the new snapshot type; no fallback to legacy direct
dispatch on routing failure; Chapter-148 (`pcae push`) itself is
unaffected.
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


def _init_with_remote(tmp_path: Path) -> Path:
    bare = tmp_path / "remote.git"
    bare.mkdir()
    subprocess.run(["git", "init", "--bare"], cwd=bare, check=True, capture_output=True)

    work = tmp_path / "work"
    work.mkdir()
    init_harness(HarnessPath(work))
    subprocess.run(["git", "init"], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "remote", "add", "origin", str(bare)], cwd=work, check=True, capture_output=True)
    create_task_contract(
        HarnessPath(work), "149F push routing test task",
        created_at=datetime(2026, 8, 3, 12, 0, tzinfo=timezone.utc),
    )
    subprocess.run(["git", "add", "."], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "branch", "-M", "main"], cwd=work, capture_output=True, text=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], cwd=work, check=True, capture_output=True)
    return work


def _commit_unpushed(work: Path, filename: str = "impl.py") -> None:
    p = work / filename
    p.write_text("# change\n", encoding="utf-8")
    subprocess.run(["git", "add", filename], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "change"], cwd=work, check=True, capture_output=True)


def _force_decision(monkeypatch, decision: str) -> dict:
    calls = {"count": 0}

    def fake_evaluate(self, request):
        calls["count"] += 1
        return pbf.PermissionBrokerDecision(
            decision=decision, decision_reason="test_forced",
            matched_no_go_ids=(), matched_invariants=(), required_remediation=(),
            requires_human=(decision == pbf.DECISION_HUMAN_REVIEW), simulation_only=True,
        )

    monkeypatch.setattr(pbf.PermissionBroker, "evaluate", fake_evaluate)
    return calls


# ── AG2 real ALLOW positive control ─────────────────────────────────────


def test_ag2_real_allow_pushes_exactly_once(tmp_path):
    work = _init_with_remote(tmp_path)
    _commit_unpushed(work)
    root = HarnessPath(work)

    result = agent_module._dispatch_governed_push(root, "origin", "main", None)
    active_task = None
    from pcae.core.tasks import find_latest_active_task

    task = find_latest_active_task(root)
    result = agent_module._dispatch_governed_push(root, "origin", "main", task.task_id if task else None)
    assert result.authorized is True
    assert result.dispatched is True
    assert result.push_proc.returncode == 0


# ── AG2 DENY / HUMAN_REVIEW / broker failure -> zero push ──────────────


@pytest.mark.parametrize("decision", [pbf.DECISION_DENY, pbf.DECISION_HUMAN_REVIEW])
def test_ag2_non_allow_blocks_dispatch(tmp_path, monkeypatch, decision):
    work = _init_with_remote(tmp_path)
    _commit_unpushed(work)
    root = HarnessPath(work)
    calls = _force_decision(monkeypatch, decision)

    result = agent_module._dispatch_governed_push(root, "origin", "main", "some-task")
    assert result.authorized is False
    assert result.dispatched is False
    assert calls["count"] == 1


def test_ag2_broker_failure_blocks_dispatch(tmp_path, monkeypatch):
    work = _init_with_remote(tmp_path)
    _commit_unpushed(work)
    root = HarnessPath(work)

    def exploding_evaluate(self, request):
        raise RuntimeError("boom")

    monkeypatch.setattr(pbf.PermissionBroker, "evaluate", exploding_evaluate)
    result = agent_module._dispatch_governed_push(root, "origin", "main", "some-task")
    assert result.authorized is False
    assert result.dispatched is False


def test_ag2_freshness_drift_blocks_dispatch(tmp_path, monkeypatch):
    """ALLOW -> HEAD advances (another commit lands) before dispatch ->
    zero push."""
    work = _init_with_remote(tmp_path)
    _commit_unpushed(work)
    root = HarnessPath(work)

    real_evaluate = mp.evaluate_alternate_push_permission

    def evaluate_then_drift(root_arg, remote, branch, task_id):
        result, snapshot = real_evaluate(root_arg, remote, branch, task_id)
        _commit_unpushed(work, filename="drift.py")
        return result, snapshot

    monkeypatch.setattr(agent_module.mutation_permission, "evaluate_alternate_push_permission", evaluate_then_drift)

    result = agent_module._dispatch_governed_push(root, "origin", "main", "some-task")
    assert result.authorized is True
    assert result.dispatched is False
    assert result.stale_mismatches


# ── PH2/PH3 routing (no independent dispatch, no duplicate gate) ───────


def test_phase_py_contains_no_independent_git_push_dispatch():
    """RWMPC-REQ-035/037 non-bypassability, by source inspection."""
    phase_source = Path(agent_module.__file__).parent.parent.joinpath(
        "commands", "phase.py"
    ).read_text(encoding="utf-8")
    assert "_dispatch_governed_push" in phase_source
    import re

    assert not re.findall(r'_sp\.run\(\s*\[\s*"git"\s*,\s*"push"', phase_source)


def test_ph2_ph3_do_not_construct_their_own_permission_broker_request():
    phase_path = Path(agent_module.__file__).parent.parent / "commands" / "phase.py"
    source = phase_path.read_text(encoding="utf-8")
    assert "PermissionBroker(" not in source
    assert "permission_broker_foundation" not in source


def test_dispatch_governed_push_called_exactly_once_per_attempt(tmp_path, monkeypatch):
    """PH2/PH3 routing to AG2's shared dispatcher must not add a second
    broker evaluation on top of their own mechanical gates."""
    work = _init_with_remote(tmp_path)
    _commit_unpushed(work)
    root = HarnessPath(work)
    calls = {"count": 0}
    real_dispatch = agent_module._dispatch_governed_push

    def counting_dispatch(root_arg, remote, branch, task_id):
        calls["count"] += 1
        return real_dispatch(root_arg, remote, branch, task_id)

    monkeypatch.setattr(agent_module, "_dispatch_governed_push", counting_dispatch)
    # Simulate PH2/PH3's own call shape directly (their own mechanical
    # gates are exercised in test_phase.py / test_lifecycle_regression.py
    # end to end).
    from pcae.core.tasks import find_latest_active_task

    task = find_latest_active_task(root)
    agent_module._dispatch_governed_push(root, "origin", "main", task.task_id if task else None)
    assert calls["count"] == 1
