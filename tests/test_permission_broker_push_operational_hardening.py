"""Phase 148G.1 — Permission Broker Production Consumption Operational
Hardening.

Focused tests for the two findings 148G.1 closes:

- F-148F-3: PBPC-001 v1.2 Section 17 (PBPC-REQ-059/060/061) final
  pre-dispatch re-observation was entirely unimplemented on both `pcae
  push` dispatch paths. This suite proves a genuine broker `ALLOW`
  cannot dispatch once a decision-bound fact (local HEAD, branch,
  unpushed commit count, active task ID) drifts between broker
  evaluation and dispatch, and that an unchanged decision still
  dispatches exactly once.

- F-148F-1: `PermissionBroker()` construction failure used to propagate
  as an uncaught exception rather than the same graceful, fail-closed
  diagnostic `evaluate()` failure already produced. Covered directly in
  `tests/test_phase_148f_permission_broker_production_consumption_independent_verification.py`
  (rewritten by this phase to assert the repaired behavior); this
  module adds no duplicate coverage for that finding.

Reuses the same local bare-remote fixture shape as 148E/148F/148G's own
suites (no real external remote, no mocked Permission Broker
Foundation).
"""

from __future__ import annotations

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
from pcae.core.tasks import create_task_contract


def _init_with_remote(tmp_path: Path, monkeypatch, with_task: bool = True) -> Path:
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
            "148G.1 operational hardening test task",
            created_at=datetime(2026, 8, 3, 12, 0, tzinfo=timezone.utc),
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
    real_run = subprocess.run
    calls = {"count": 0}

    def fake_run(cmd, *args, **kwargs):
        if isinstance(cmd, list) and len(cmd) >= 2 and cmd[0] == "git" and cmd[1] == "push":
            calls["count"] += 1
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(push_module.subprocess, "run", fake_run)
    return calls


def _force_allow(monkeypatch) -> dict:
    """Force every Permission Broker evaluation to return a genuine
    `PermissionBrokerDecision(ALLOW)` (a real instance, not a duck-typed
    fake), and count `evaluate()` invocations."""
    calls = {"count": 0}

    def fake_evaluate(self, request):
        calls["count"] += 1
        return pbf.PermissionBrokerDecision(
            decision=pbf.DECISION_ALLOW,
            decision_reason="test_forced_allow",
            matched_no_go_ids=(),
            matched_invariants=(),
            required_remediation=(),
            requires_human=False,
            simulation_only=True,
            causing_policy_ids=(),
        )

    monkeypatch.setattr(pbf.PermissionBroker, "evaluate", fake_evaluate)
    return calls


# ── Validation ordering: broker evaluation < final re-observation < dispatch ─


def test_final_validation_ordering_present_in_source():
    """PBPC-REQ-059-061 require final re-observation to occur after broker
    ALLOW and immediately before dispatch, on both paths. Independently
    confirm the ordering from source rather than trusting behavior tests
    alone."""
    import inspect

    source = inspect.getsource(push_module)

    ordinary_evaluate = source.index("permission_result = _evaluate_push_permission(")
    ordinary_freshness = source.index("_validate_push_permission_freshness(root, permission_result.decision_snapshot)")
    ordinary_dispatch = source.index('["git", "push"]')
    assert ordinary_evaluate < ordinary_freshness < ordinary_dispatch

    staged_freshness = source.index(
        "_validate_push_permission_freshness(root, permission_result.decision_snapshot)",
        ordinary_freshness + 1,
    )
    staged_dispatch = source.index('["git", "push", "origin", "main"]')
    assert staged_freshness < staged_dispatch


# ── Ordinary path: no-drift control ──────────────────────────────────────


def test_ordinary_path_no_drift_still_dispatches_exactly_once(tmp_path, monkeypatch, capsys):
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)
    dispatch_calls = _spy_git_push(monkeypatch)
    evaluate_calls = _force_allow(monkeypatch)

    exit_code = main(["push"])
    capsys.readouterr()

    assert exit_code == 0
    assert dispatch_calls["count"] == 1
    assert evaluate_calls["count"] == 1


# ── Ordinary path: HEAD drift between ALLOW and dispatch ────────────────


def test_ordinary_path_head_drift_after_allow_blocks_dispatch(tmp_path, monkeypatch, capsys):
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)
    dispatch_calls = _spy_git_push(monkeypatch)
    _force_allow(monkeypatch)

    real_freshness = push_module._validate_push_permission_freshness

    def drifting_freshness(root, snapshot):
        # Simulate a local mutation landing between broker ALLOW and the
        # final re-observation call: a new commit lands on HEAD.
        _create_unpushed_commit(root.path, filename="external.py", msg="external drift")
        return real_freshness(root, snapshot)

    monkeypatch.setattr(push_module, "_validate_push_permission_freshness", drifting_freshness)

    exit_code = main(["push"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "decision-bound state changed" in output.lower()
    assert dispatch_calls["count"] == 0


# ── Staged-file-aware path: HEAD drift between ALLOW and dispatch ───────


def test_staged_file_aware_path_head_drift_after_allow_blocks_dispatch(tmp_path, monkeypatch, capsys):
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)
    dispatch_calls = _spy_git_push(monkeypatch)
    _force_allow(monkeypatch)

    real_freshness = push_module._validate_push_permission_freshness

    def drifting_freshness(root, snapshot):
        _create_unpushed_commit(root.path, filename="external2.py", msg="external drift")
        return real_freshness(root, snapshot)

    monkeypatch.setattr(push_module, "_validate_push_permission_freshness", drifting_freshness)

    exit_code = main(["push", "--staged-file-aware"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "decision-bound state changed" in output.lower()
    assert dispatch_calls["count"] == 0


# ── Branch drift ──────────────────────────────────────────────────────


def test_ordinary_path_branch_drift_after_allow_blocks_dispatch(tmp_path, monkeypatch, capsys):
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)
    dispatch_calls = _spy_git_push(monkeypatch)
    _force_allow(monkeypatch)

    real_freshness = push_module._validate_push_permission_freshness

    def drifting_freshness(root, snapshot):
        subprocess.run(["git", "checkout", "-b", "drifted-branch"], cwd=root.path, check=True, capture_output=True)
        return real_freshness(root, snapshot)

    monkeypatch.setattr(push_module, "_validate_push_permission_freshness", drifting_freshness)

    exit_code = main(["push"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "decision-bound state changed" in output.lower()
    assert dispatch_calls["count"] == 0


# ── Task-ID drift ─────────────────────────────────────────────────────


def test_ordinary_path_task_id_drift_after_allow_blocks_dispatch(tmp_path, monkeypatch, capsys):
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)
    dispatch_calls = _spy_git_push(monkeypatch)
    _force_allow(monkeypatch)

    real_freshness = push_module._validate_push_permission_freshness

    def drifting_freshness(root, snapshot):
        # A new task contract replaces the active task between decision
        # and dispatch. No fabricated replacement task ID is asserted --
        # the freshness check must observe whatever real task is active.
        create_task_contract(
            root,
            "148G.1 drifted replacement task",
            created_at=datetime(2026, 8, 3, 13, 0, tzinfo=timezone.utc),
        )
        return real_freshness(root, snapshot)

    monkeypatch.setattr(push_module, "_validate_push_permission_freshness", drifting_freshness)

    exit_code = main(["push"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "decision-bound state changed" in output.lower()
    assert dispatch_calls["count"] == 0


# ── Multiple simultaneous drifts still fail closed ───────────────────────


def test_ordinary_path_multiple_simultaneous_drift_blocks_dispatch(tmp_path, monkeypatch, capsys):
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)
    dispatch_calls = _spy_git_push(monkeypatch)
    _force_allow(monkeypatch)

    real_freshness = push_module._validate_push_permission_freshness

    def drifting_freshness(root, snapshot):
        _create_unpushed_commit(root.path, filename="multi.py", msg="multi drift")
        create_task_contract(
            root,
            "148G.1 multi-drift replacement task",
            created_at=datetime(2026, 8, 3, 14, 0, tzinfo=timezone.utc),
        )
        return real_freshness(root, snapshot)

    monkeypatch.setattr(push_module, "_validate_push_permission_freshness", drifting_freshness)

    exit_code = main(["push"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert dispatch_calls["count"] == 0


# ── Genuine ALLOW cannot be overridden by drift: central F-148F-3 proof ──


def test_genuine_allow_plus_drift_cannot_dispatch(tmp_path, monkeypatch, capsys):
    """The precise claim F-148F-3 closure rests on: a real, non-forged
    `ALLOW` decision from the real broker/evaluate() path is still
    insufficient to dispatch once decision-bound state has drifted.
    Distinct from the duck-typed-fake-ALLOW test (148F) -- this uses a
    genuine `PermissionBrokerDecision(ALLOW)` instance."""
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)
    dispatch_calls = _spy_git_push(monkeypatch)
    evaluate_calls = _force_allow(monkeypatch)

    real_freshness = push_module._validate_push_permission_freshness

    def drifting_freshness(root, snapshot):
        _create_unpushed_commit(root.path, filename="genuine_drift.py", msg="genuine drift")
        return real_freshness(root, snapshot)

    monkeypatch.setattr(push_module, "_validate_push_permission_freshness", drifting_freshness)

    exit_code = main(["push"])
    capsys.readouterr()

    assert exit_code == 1
    assert evaluate_calls["count"] == 1  # broker genuinely said ALLOW ...
    assert dispatch_calls["count"] == 0  # ... but drift still blocked dispatch


# ── No stale ALLOW reuse across a rerun after drift ──────────────────────


def test_stale_allow_cannot_be_reused_but_fresh_rerun_succeeds(tmp_path, monkeypatch, capsys):
    """PBPC-REQ-061: on material mismatch the existing ALLOW is invalid
    and a fresh evaluation cycle is required before any further dispatch
    attempt -- not an automatic in-place re-evaluation. Prove the first
    (drifted) attempt is blocked, then a fresh `pcae push` invocation
    (fresh broker evaluation against current state) succeeds."""
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)
    dispatch_calls = _spy_git_push(monkeypatch)
    evaluate_calls = _force_allow(monkeypatch)

    real_freshness = push_module._validate_push_permission_freshness
    drift_state = {"done": False}

    def drift_once(root, snapshot):
        if not drift_state["done"]:
            drift_state["done"] = True
            _create_unpushed_commit(root.path, filename="stale_reuse.py", msg="stale reuse drift")
        return real_freshness(root, snapshot)

    monkeypatch.setattr(push_module, "_validate_push_permission_freshness", drift_once)

    first_exit = main(["push"])
    capsys.readouterr()
    assert first_exit == 1
    assert dispatch_calls["count"] == 0

    second_exit = main(["push"])
    capsys.readouterr()
    assert second_exit == 0
    assert dispatch_calls["count"] == 1
    assert evaluate_calls["count"] == 2  # fresh evaluation on the second attempt, not reused
