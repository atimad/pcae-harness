"""Tests for Phase 148E — Permission Broker Production Consumption
Implementation.

Verifies PBPC-001 v1.2 production consumption for both real `pcae push`
git-push dispatch sites (`run_push()` and `_run_push_staged_file_aware()`):
canonical request construction, ALLOW/DENY/HUMAN_REVIEW/broker-failure
consumption, non-bypassability, exactly-once evaluation and dispatch, no
stale decision reuse, and POL-004/POL-005 regression. Uses local bare
remotes for real (non-network) push dispatch -- no mocked remote mutation
beyond a local filesystem bare repository.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

pytestmark = [pytest.mark.slow, pytest.mark.integration]

from pcae.cli import main
from pcae.commands import push as push_module
from pcae.commands.init import init_harness
from pcae.core import permission_broker_foundation as pbf
from pcae.core.paths import HarnessPath
from pcae.core.tasks import close_active_task, create_task_contract, find_latest_active_task


# ── fixtures / helpers ──────────────────────────────────────────────────


def _init_with_remote(tmp_path: Path, monkeypatch, with_task: bool = True) -> Path:
    """A PCAE repo with a local bare remote and (by default) an active
    task contract, so the canonical `pcae push` request's `task_id` is
    populated and POL-001 does not deny."""
    bare = tmp_path / "remote.git"
    bare.mkdir()
    subprocess.run(["git", "init", "--bare"], cwd=bare, check=True, capture_output=True)

    work = tmp_path / "work"
    work.mkdir()
    init_harness(HarnessPath(work))
    subprocess.run(["git", "init"], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "remote", "add", "origin", str(bare)], cwd=work, check=True, capture_output=True)
    if with_task:
        create_task_contract(
            HarnessPath(work),
            "PBPC production consumption test task",
            created_at=datetime(2026, 8, 2, 18, 0, tzinfo=timezone.utc),
        )
    subprocess.run(["git", "add", "."], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "branch", "-M", "main"], cwd=work, capture_output=True, text=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], cwd=work, check=True, capture_output=True)
    monkeypatch.chdir(work)
    return work


def _create_unpushed_commit(root: Path, filename: str = "impl.py", msg: str = "implementation") -> None:
    p = root / filename
    p.write_text(f"# {msg}\n", encoding="utf-8")
    subprocess.run(["git", "add", filename], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", msg, "--", filename], cwd=root, check=True, capture_output=True)


def _spy_git_push(monkeypatch) -> dict:
    """Count real `git push` invocations without preventing them --
    everything else passes through to the real `subprocess.run`."""
    real_run = subprocess.run
    calls = {"count": 0}

    def fake_run(cmd, *args, **kwargs):
        if isinstance(cmd, list) and len(cmd) >= 2 and cmd[0] == "git" and cmd[1] == "push":
            calls["count"] += 1
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(push_module.subprocess, "run", fake_run)
    return calls


def _force_decision(monkeypatch, decision: str, causing_policy_ids: tuple = ()) -> dict:
    """Force every Permission Broker evaluation to return a fixed decision,
    and count how many times `evaluate()` was actually called."""
    calls = {"count": 0}

    def fake_evaluate(self, request):
        calls["count"] += 1
        return pbf.PermissionBrokerDecision(
            decision=decision,
            decision_reason="test_forced_decision",
            matched_no_go_ids=(),
            matched_invariants=(),
            required_remediation=(),
            requires_human=(decision == pbf.DECISION_HUMAN_REVIEW),
            simulation_only=True,
            causing_policy_ids=causing_policy_ids,
        )

    monkeypatch.setattr(pbf.PermissionBroker, "evaluate", fake_evaluate)
    return calls


def _capture_requests(monkeypatch) -> list:
    """Spy on `build_permission_broker_request` to capture every canonical
    request constructed by the adapter, while still constructing it for
    real (not a substitute/mocked object)."""
    captured: list = []
    real_build = pbf.build_permission_broker_request

    def spy_build(**kwargs):
        request = real_build(**kwargs)
        captured.append(request)
        return request

    monkeypatch.setattr(pbf, "build_permission_broker_request", spy_build)
    return captured


# ── canonical request shape ─────────────────────────────────────────────


def test_ordinary_path_canonical_request_shape(tmp_path, monkeypatch, capsys):
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)
    captured = _capture_requests(monkeypatch)

    exit_code = main(["push"])
    capsys.readouterr()

    assert exit_code == 0
    assert len(captured) == 1
    request = captured[0]
    assert request.action_type == pbf.ACTION_PUSH
    assert request.execution_class == pbf.EXECUTION_CLASS_MUTATION
    assert request.approval_present is False
    assert request.simulation_only is True
    assert request.requested_component == "COMP-001"
    assert request.requested_capability == "pcae_push"
    assert request.task_id is not None


def test_staged_file_aware_canonical_request_shape(tmp_path, monkeypatch, capsys):
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)
    captured = _capture_requests(monkeypatch)

    exit_code = main(["push", "--staged-file-aware"])
    capsys.readouterr()

    assert exit_code == 0
    assert len(captured) == 1
    request = captured[0]
    assert request.action_type == pbf.ACTION_PUSH
    assert request.execution_class == pbf.EXECUTION_CLASS_MUTATION
    assert request.approval_present is False
    assert request.simulation_only is True
    assert request.task_id is not None


# ── ALLOW: real dispatch exactly once ───────────────────────────────────


def test_ordinary_path_allow_dispatches_exactly_once(tmp_path, monkeypatch, capsys):
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)
    dispatch_calls = _spy_git_push(monkeypatch)

    exit_code = main(["push"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "PUSH EXECUTED" in output
    assert dispatch_calls["count"] == 1


def test_staged_file_aware_allow_dispatches_exactly_once(tmp_path, monkeypatch, capsys):
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)
    dispatch_calls = _spy_git_push(monkeypatch)

    exit_code = main(["push", "--staged-file-aware", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["push_staged_file_aware_status"] == "pushed"
    assert dispatch_calls["count"] == 1


# ── DENY: zero dispatch ──────────────────────────────────────────────────


def test_ordinary_path_deny_blocks_dispatch(tmp_path, monkeypatch, capsys):
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)
    dispatch_calls = _spy_git_push(monkeypatch)
    _force_decision(monkeypatch, pbf.DECISION_DENY, causing_policy_ids=("POL-001",))

    exit_code = main(["push"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "permission denied" in output.lower()
    assert dispatch_calls["count"] == 0


def test_staged_file_aware_deny_blocks_dispatch(tmp_path, monkeypatch, capsys):
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)
    dispatch_calls = _spy_git_push(monkeypatch)
    _force_decision(monkeypatch, pbf.DECISION_DENY, causing_policy_ids=("POL-001",))

    exit_code = main(["push", "--staged-file-aware", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert output["push_staged_file_aware_status"] == "permission_denied"
    assert dispatch_calls["count"] == 0


# ── HUMAN_REVIEW: zero dispatch, no interactive override ────────────────


def test_ordinary_path_human_review_blocks_dispatch(tmp_path, monkeypatch, capsys):
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)
    dispatch_calls = _spy_git_push(monkeypatch)
    _force_decision(monkeypatch, pbf.DECISION_HUMAN_REVIEW, causing_policy_ids=("POL-004",))

    exit_code = main(["push"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "human review required" in output.lower()
    assert dispatch_calls["count"] == 0


def test_staged_file_aware_human_review_blocks_dispatch(tmp_path, monkeypatch, capsys):
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)
    dispatch_calls = _spy_git_push(monkeypatch)
    _force_decision(monkeypatch, pbf.DECISION_HUMAN_REVIEW, causing_policy_ids=("POL-004",))

    exit_code = main(["push", "--staged-file-aware", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert output["push_staged_file_aware_status"] == "permission_denied"
    assert dispatch_calls["count"] == 0


# ── broker failure: fail closed, zero dispatch ───────────────────────────


def test_ordinary_path_broker_exception_blocks_dispatch(tmp_path, monkeypatch, capsys):
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)
    dispatch_calls = _spy_git_push(monkeypatch)

    def raising_evaluate(self, request):
        raise RuntimeError("simulated broker failure")

    monkeypatch.setattr(pbf.PermissionBroker, "evaluate", raising_evaluate)

    exit_code = main(["push"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "evaluation failed" in output.lower()
    assert dispatch_calls["count"] == 0


def test_staged_file_aware_broker_exception_blocks_dispatch(tmp_path, monkeypatch, capsys):
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)
    dispatch_calls = _spy_git_push(monkeypatch)

    def raising_evaluate(self, request):
        raise RuntimeError("simulated broker failure")

    monkeypatch.setattr(pbf.PermissionBroker, "evaluate", raising_evaluate)

    exit_code = main(["push", "--staged-file-aware", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert output["push_staged_file_aware_status"] == "permission_denied"
    assert output["permission_decision"] == "BROKER_FAILURE"
    assert dispatch_calls["count"] == 0


def test_invalid_broker_result_blocks_dispatch(tmp_path, monkeypatch, capsys):
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)
    dispatch_calls = _spy_git_push(monkeypatch)

    def invalid_evaluate(self, request):
        return "not-a-decision"

    monkeypatch.setattr(pbf.PermissionBroker, "evaluate", invalid_evaluate)

    exit_code = main(["push"])
    capsys.readouterr()

    assert exit_code == 1
    assert dispatch_calls["count"] == 0


# ── POL-004 / POL-005 regression ─────────────────────────────────────────


def test_canonical_push_request_pol_004_not_applicable(tmp_path, monkeypatch):
    root = HarnessPath.cwd()
    result = push_module._evaluate_push_permission(root=root, task_id="task-x")
    assert result.decision is not None
    assert "POL-004" in result.decision.non_applicable_policy_ids
    assert result.request.approval_present is False


def test_canonical_push_request_simulation_only_true_avoids_pol_005_deny(tmp_path):
    root = HarnessPath.cwd()
    result = push_module._evaluate_push_permission(root=root, task_id="task-x")
    assert result.request.simulation_only is True
    assert "POL-005" not in (result.decision.causing_policy_ids if result.decision else ())


def test_pol_005_still_denies_simulation_only_false():
    """Foundation regression, not an adapter behavior: this proves the
    adapter's fixed simulation_only=True (F-148C.8-1) is load-bearing --
    if it were ever accidentally flipped, POL-005 would unconditionally
    deny."""
    request = pbf.build_permission_broker_request(
        action_type=pbf.ACTION_PUSH,
        execution_class=pbf.EXECUTION_CLASS_MUTATION,
        requested_component="COMP-001",
        requested_capability="pcae_push",
        task_id="task-x",
        evidence_available=True,
        approval_present=False,
        simulation_only=False,
    )
    decision = pbf.PermissionBroker().evaluate(request)
    assert decision.decision == pbf.DECISION_DENY
    assert "POL-005" in decision.causing_policy_ids


# ── non-bypassability ─────────────────────────────────────────────────────


def test_ordinary_path_non_bypassable_for_every_non_allow_outcome(tmp_path, monkeypatch, capsys):
    for decision_value in (pbf.DECISION_DENY, pbf.DECISION_HUMAN_REVIEW):
        sub = tmp_path / decision_value
        sub.mkdir()
        work = _init_with_remote(sub, monkeypatch)
        _create_unpushed_commit(work)
        dispatch_calls = _spy_git_push(monkeypatch)
        _force_decision(monkeypatch, decision_value)

        exit_code = main(["push"])
        capsys.readouterr()

        assert exit_code == 1
        assert dispatch_calls["count"] == 0


def test_staged_file_aware_non_bypassable_for_every_non_allow_outcome(tmp_path, monkeypatch, capsys):
    for decision_value in (pbf.DECISION_DENY, pbf.DECISION_HUMAN_REVIEW):
        sub = tmp_path / decision_value
        sub.mkdir()
        work = _init_with_remote(sub, monkeypatch)
        _create_unpushed_commit(work)
        dispatch_calls = _spy_git_push(monkeypatch)
        _force_decision(monkeypatch, decision_value)

        exit_code = main(["push", "--staged-file-aware"])
        capsys.readouterr()

        assert exit_code == 1
        assert dispatch_calls["count"] == 0


def test_staged_file_aware_mechanical_checks_still_block_before_broker(tmp_path, monkeypatch, capsys):
    """Existing mechanical checks (phase-report identity here) must
    continue to abort before the broker is ever constructed -- not
    merely 'still blocks', but blocks via the pre-existing code path."""
    work = _init_with_remote(tmp_path, monkeypatch)
    # A completed-phase task with no canonical report triggers the
    # existing phase-report-identity mechanical gate.
    root = HarnessPath(work)
    create_task_contract(
        root,
        "Phase 900Z — Reproduction Phase",
        created_at=datetime(2026, 8, 2, 19, 0, tzinfo=timezone.utc),
    )
    close_active_task(find_latest_active_task(root))
    create_task_contract(
        root,
        "Idle: awaiting next governed phase (post-900z)",
        created_at=datetime(2026, 8, 2, 19, 5, tzinfo=timezone.utc),
        mode="idle",
    )
    subprocess.run(["git", "add", "."], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "close phase"], cwd=work, check=True, capture_output=True)

    captured = _capture_requests(monkeypatch)
    dispatch_calls = _spy_git_push(monkeypatch)

    exit_code = main(["push", "--staged-file-aware"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "phase report identity" in output.lower()
    assert len(captured) == 0
    assert dispatch_calls["count"] == 0


# ── exactly-once evaluation ──────────────────────────────────────────────


def test_ordinary_path_evaluates_broker_exactly_once(tmp_path, monkeypatch, capsys):
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)
    evaluate_calls = _force_decision(monkeypatch, pbf.DECISION_ALLOW)

    exit_code = main(["push"])
    capsys.readouterr()

    assert exit_code == 0
    assert evaluate_calls["count"] == 1


def test_staged_file_aware_evaluates_broker_exactly_once(tmp_path, monkeypatch, capsys):
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)
    evaluate_calls = _force_decision(monkeypatch, pbf.DECISION_ALLOW)

    exit_code = main(["push", "--staged-file-aware"])
    capsys.readouterr()

    assert exit_code == 0
    assert evaluate_calls["count"] == 1


# ── no stale decision reuse ──────────────────────────────────────────────


def test_ordinary_path_no_stale_decision_reuse(tmp_path, monkeypatch, capsys):
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work, filename="first.py", msg="first")
    dispatch_calls = _spy_git_push(monkeypatch)

    exit_code_1 = main(["push"])
    capsys.readouterr()
    assert exit_code_1 == 0
    assert dispatch_calls["count"] == 1

    # Second attempt: force DENY this time -- must independently
    # re-evaluate, never reuse attempt 1's ALLOW.
    _create_unpushed_commit(work, filename="second.py", msg="second")
    _force_decision(monkeypatch, pbf.DECISION_DENY, causing_policy_ids=("POL-001",))

    exit_code_2 = main(["push"])
    capsys.readouterr()

    assert exit_code_2 == 1
    assert dispatch_calls["count"] == 1  # unchanged -- second attempt did not dispatch
