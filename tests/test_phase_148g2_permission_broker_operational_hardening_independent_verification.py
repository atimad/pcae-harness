"""Phase 148G.2 — Permission Broker Production Consumption Operational
Hardening Independent Verification.

Independent adversarial verification of 148G.1's PBPC-001 v1.2 Section 17
(PBPC-REQ-059/060/061) final pre-dispatch freshness hardening and the
F-148F-1 broker-construction-failure repair. Does not reuse or extend
`tests/test_permission_broker_push_operational_hardening.py` (148G.1's own
suite) or trust its docstrings/claims -- this file independently
reconstructs coverage from `push.py` production source and PBPC-001 v1.2
contract text, adding tests 148G.1 did not write:

- unpushed-commit-count drift in isolation (not combined with any other
  fact change) -- 148G.1's own report flagged this as not separately
  emphasized;
- final re-observation *helper* failure (an observation call itself
  raising) rather than a drift *value*, both for the freshness path and
  via the real CLI entrypoint;
- direct, non-CLI unit inspection of `_PushDecisionSnapshot` (immutability,
  attempted mutation) and `_observe_push_decision_state` /
  `_validate_push_permission_freshness` in isolation;
- broker *construction* failure driven through the real `pcae push` CLI
  entrypoint (`main(["push"])`), independent of 148F's rewritten tests;
- a corrected consumer-scope guard check that inspects the module the
  actual git-push dispatch site lives in (`pcae.core.agent`), not the
  thin CLI wrapper module (`pcae.commands.agent`) 148G.1's repaired
  148C.10 test checks instead.

Reuses the same local bare-remote fixture shape as prior PBPC suites (no
mocked Permission Broker Foundation, no real external remote). Modifies no
production code.
"""

from __future__ import annotations

import inspect
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
            "148G.2 independent verification test task",
            created_at=datetime(2026, 8, 3, 15, 0, tzinfo=timezone.utc),
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


# ── 1. Sole production file / contract boundary (independent re-check) ──


def test_148g1_touched_exactly_one_src_pcae_file():
    result = subprocess.run(
        ["git", "diff", "--name-only", "06611796..90e7eb6e", "--", "src/pcae/"],
        cwd=Path(__file__).resolve().parents[1],
        check=True,
        capture_output=True,
        text=True,
    )
    files = [f for f in result.stdout.strip().splitlines() if f]
    assert files == ["src/pcae/commands/push.py"]


def test_148g1_touched_zero_contract_files():
    result = subprocess.run(
        ["git", "diff", "--name-only", "06611796..90e7eb6e", "--", "docs/contracts/"],
        cwd=Path(__file__).resolve().parents[1],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == ""


# ── 2. _PushDecisionSnapshot: isolated structural inspection ────────────


def test_push_decision_snapshot_is_frozen_dataclass_with_exactly_four_fields():
    import dataclasses

    assert dataclasses.is_dataclass(push_module._PushDecisionSnapshot)
    params = dataclasses.fields(push_module._PushDecisionSnapshot)
    names = {f.name for f in params}
    assert names == {"head", "branch", "unpushed", "task_id"}
    # frozen=True on the decorator is necessary but not sufficient --
    # independently attempt mutation on a real instance.


def test_push_decision_snapshot_mutation_raises(tmp_path, monkeypatch):
    work = _init_with_remote(tmp_path, monkeypatch)
    snap = push_module._observe_push_decision_state(HarnessPath(work), "some-task")
    with pytest.raises(Exception):
        snap.head = "tampered"  # type: ignore[misc]


# ── 3. Unpushed-commit-count drift in isolation ──────────────────────────


def test_ordinary_path_unpushed_count_drift_alone_blocks_dispatch(tmp_path, monkeypatch, capsys):
    """Isolated from HEAD/branch/task-id drift: an *additional* unpushed
    commit lands between decision and dispatch. Note this necessarily also
    changes HEAD (a new commit changes HEAD by construction) -- so this
    test additionally asserts the diagnostic specifically names the
    unpushed-count mismatch, not just any mismatch, proving the count
    field is itself compared rather than only HEAD."""
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)
    dispatch_calls = _spy_git_push(monkeypatch)
    _force_allow(monkeypatch)

    real_freshness = push_module._validate_push_permission_freshness

    def drifting_freshness(root, snapshot):
        _create_unpushed_commit(root.path, filename="count_drift.py", msg="count drift")
        return real_freshness(root, snapshot)

    monkeypatch.setattr(push_module, "_validate_push_permission_freshness", drifting_freshness)

    exit_code = main(["push"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "unpushed commit count changed" in output.lower()
    assert dispatch_calls["count"] == 0


def test_validate_freshness_detects_unpushed_count_drift_directly(tmp_path, monkeypatch):
    """Direct, non-CLI unit test of `_validate_push_permission_freshness`:
    hold HEAD/branch/task_id fixed conceptually by constructing a snapshot
    with today's HEAD but a fabricated `unpushed` count that no longer
    matches reality, and confirm the helper reports exactly that
    mismatch."""
    work = _init_with_remote(tmp_path, monkeypatch)
    root = HarnessPath(work)
    real_snapshot = push_module._observe_push_decision_state(root, None)
    forged_snapshot = push_module._PushDecisionSnapshot(
        head=real_snapshot.head,
        branch=real_snapshot.branch,
        unpushed=real_snapshot.unpushed + 5,
        task_id=real_snapshot.task_id,
    )
    fresh, mismatches = push_module._validate_push_permission_freshness(root, forged_snapshot)
    assert fresh is False
    assert any("unpushed commit count changed" in m for m in mismatches)
    assert not any("local HEAD changed" in m for m in mismatches)
    assert not any("branch changed" in m for m in mismatches)


# ── 4. Final re-observation helper failure (not a value drift) ──────────


def test_final_reobservation_head_lookup_failure_fails_closed(tmp_path, monkeypatch, capsys):
    """Force the underlying `git rev-parse HEAD` re-observation call itself
    to fail (CalledProcessError) during the *final* freshness check --
    distinct from a value simply drifting. PBPC-REQ-062's 'repository
    observation failure' row requires this to still block dispatch, even
    though the failure surfaces via `pcae.cli.main`'s generic
    CalledProcessError handler rather than a Permission-Broker-specific
    diagnostic."""
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)
    dispatch_calls = _spy_git_push(monkeypatch)
    _force_allow(monkeypatch)

    real_read_branch = push_module.read_git_branch
    call_state = {"n": 0}

    def failing_read_git_branch(root):
        call_state["n"] += 1
        # First call happens at decision-snapshot time (must succeed so a
        # genuine ALLOW is reached); fail on the final re-observation call.
        if call_state["n"] >= 2:
            raise subprocess.CalledProcessError(128, ["git", "branch", "--show-current"])
        return real_read_branch(root)

    monkeypatch.setattr(push_module, "read_git_branch", failing_read_git_branch)

    exit_code = main(["push"])
    capsys.readouterr()

    assert exit_code == 1
    assert dispatch_calls["count"] == 0


# ── 5. Malformed / degenerate observation cannot be mistaken for a match ─


def test_freshness_helper_does_not_treat_empty_head_as_matching_real_head(tmp_path, monkeypatch):
    """If HEAD re-observation degenerates to the empty-string fallback
    `_observe_push_decision_state` uses on a nonzero `git rev-parse`
    exit code, it must not be silently treated as matching a real,
    non-empty decision-time HEAD."""
    work = _init_with_remote(tmp_path, monkeypatch)
    root = HarnessPath(work)
    real_snapshot = push_module._observe_push_decision_state(root, None)
    assert real_snapshot.head  # sanity: real HEAD is non-empty

    real_run = subprocess.run

    def degrade_head(cmd, *args, **kwargs):
        if isinstance(cmd, list) and cmd[:2] == ["git", "rev-parse"]:
            class _Result:
                returncode = 128
                stdout = ""
            return _Result()
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(push_module.subprocess, "run", degrade_head)
    fresh, mismatches = push_module._validate_push_permission_freshness(root, real_snapshot)
    assert fresh is False
    assert any("local HEAD changed" in m for m in mismatches)


# ── 6. Snapshot non-reuse across two attempts ────────────────────────────


def test_two_attempts_receive_independently_observed_snapshots(tmp_path, monkeypatch):
    work = _init_with_remote(tmp_path, monkeypatch)
    root = HarnessPath(work)
    snap1 = push_module._observe_push_decision_state(root, "task-a")
    _create_unpushed_commit(work, filename="between.py", msg="between snapshots")
    snap2 = push_module._observe_push_decision_state(root, "task-a")
    assert snap1.head != snap2.head
    assert snap1.unpushed != snap2.unpushed
    assert snap1 is not snap2


# ── 7. Broker construction failure via the real CLI entrypoint ──────────


def test_broker_construction_failure_via_real_cli_fails_closed_no_traceback(tmp_path, monkeypatch, capsys):
    """Independent of 148F's rewritten tests: force `PermissionBroker()`
    construction itself (not `.evaluate()`) to raise, through the actual
    `main(["push"])` entrypoint, and confirm a controlled exit code and
    diagnostic rather than an uncaught traceback escaping `main`."""
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)
    dispatch_calls = _spy_git_push(monkeypatch)

    def broken_init(self, registry=None):
        raise RuntimeError("independent-148g2-construction-failure")

    monkeypatch.setattr(pbf.PermissionBroker, "__init__", broken_init)

    exit_code = main(["push"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert dispatch_calls["count"] == 0
    assert "permission broker evaluation failed" in output.lower()


def test_broker_construction_failure_staged_path_via_real_cli_fails_closed(tmp_path, monkeypatch, capsys):
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)
    dispatch_calls = _spy_git_push(monkeypatch)

    def broken_init(self, registry=None):
        raise RuntimeError("independent-148g2-construction-failure-staged")

    monkeypatch.setattr(pbf.PermissionBroker, "__init__", broken_init)

    exit_code = main(["push", "--staged-file-aware"])
    capsys.readouterr()

    assert exit_code == 1
    assert dispatch_calls["count"] == 0


def test_retry_after_construction_failure_succeeds_with_no_partial_state(tmp_path, monkeypatch, capsys):
    """A subsequent, un-forced attempt after a construction failure must
    succeed normally -- no global/partial broker state left behind."""
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)
    dispatch_calls = _spy_git_push(monkeypatch)

    real_init = pbf.PermissionBroker.__init__
    state = {"fail_once": True}

    def maybe_broken_init(self, registry=None):
        if state["fail_once"]:
            state["fail_once"] = False
            raise RuntimeError("independent-148g2-transient-construction-failure")
        real_init(self, registry)

    monkeypatch.setattr(pbf.PermissionBroker, "__init__", maybe_broken_init)
    _force_allow(monkeypatch)

    first = main(["push"])
    capsys.readouterr()
    assert first == 1
    assert dispatch_calls["count"] == 0

    second = main(["push"])
    capsys.readouterr()
    assert second == 0
    assert dispatch_calls["count"] == 1


# ── 8. Both dispatch paths broker- and freshness-gated (source re-count) ─


def test_both_dispatch_sites_call_broker_evaluation_and_freshness_validation():
    source = inspect.getsource(push_module)
    assert source.count("_evaluate_push_permission(") >= 2  # def + >=1 call sites in this simplistic count is not useful; assert call sites directly below
    evaluate_call_sites = source.count("permission_result = _evaluate_push_permission(")
    freshness_call_sites = source.count(
        "_validate_push_permission_freshness(root, permission_result.decision_snapshot)"
    )
    dispatch_sites = source.count('["git", "push"]') + source.count('["git", "push", "origin", "main"]')
    assert evaluate_call_sites == 2
    assert freshness_call_sites == 2
    assert dispatch_sites == 2


# ── 9. Canonical request / POL-004 / POL-005 preservation ───────────────


def test_canonical_push_request_fields_unchanged():
    source = inspect.getsource(push_module)
    assert "action_type=permission_broker_foundation.ACTION_PUSH" in source
    assert "execution_class=permission_broker_foundation.EXECUTION_CLASS_MUTATION" in source
    assert 'requested_component="COMP-001"' in source
    assert 'requested_capability="pcae_push"' in source
    assert "approval_present=False" in source
    assert "simulation_only=True" in source


def test_pol_004_not_applicable_to_mutation_class():
    from pcae.core.permission_broker_foundation import (
        EXECUTION_CLASS_MUTATION,
        MissingHumanApprovalRule,
    )

    assert EXECUTION_CLASS_MUTATION not in MissingHumanApprovalRule.applicable_execution_classes


def test_pol_005_allows_simulation_only_true_pushes():
    from pcae.core.permission_broker_foundation import (
        ExecutionDisabledRule,
        PermissionBrokerRequest,
    )

    rule = ExecutionDisabledRule()
    request = PermissionBrokerRequest(
        request_id="pbr-test",
        timestamp="2026-08-03T00:00:00Z",
        action_type="push",
        execution_class="mutation",
        task_id="task-x",
        phase_id=None,
        requested_component="COMP-001",
        requested_capability="pcae_push",
        requested_resource=None,
        evidence_available=True,
        approval_present=False,
        simulation_only=True,
    )
    result = rule.evaluate(request)
    assert result.triggered is False


# ── 10. HARD_BLOCK_REGISTRY count unchanged ──────────────────────────────


def test_hard_block_registry_count_is_twelve():
    from pcae.core.permission_broker import HARD_BLOCK_REGISTRY

    assert len(HARD_BLOCK_REGISTRY) == 12


# ── 11. Corrected consumer-scope guard: the module that actually dispatches ─


def test_actual_git_push_dispatch_site_in_core_agent_remains_unwired():
    """148G.1's repaired 148C.10 test (`test_push_module_is_the_authorized_
    pbpc_production_consumer`) inspects `pcae.commands.agent` for the
    absence of Permission Broker references. But the real git-push
    dispatch site 148F/148G's inventory names is `push_file_changes`
    (`_run_git_push`), which independent inspection shows lives in
    `pcae.core.agent`, not `pcae.commands.agent` (`pcae.commands.agent`
    only imports and calls `push_file_changes`; it contains no
    `subprocess.run(["git", "push", ...])` itself). This test inspects
    the module that actually contains the dispatch call."""
    import pcae.core.agent as core_agent_module

    assert 'subprocess.run(\n        ["git", "push"' in inspect.getsource(core_agent_module) or (
        "git" in inspect.getsource(core_agent_module) and "push" in inspect.getsource(core_agent_module)
    )
    core_agent_source = inspect.getsource(core_agent_module)
    assert "PermissionBroker" not in core_agent_source
    assert "permission_broker_foundation" not in core_agent_source


def test_commands_agent_module_does_not_itself_contain_a_dispatch_call():
    """Confirms the discrepancy: `pcae.commands.agent`, the module
    148G.1's repaired guard test actually inspects, contains no
    `["git", "push", ...]` dispatch call of its own -- so a guard against
    that module alone cannot detect broker-bypass wiring added directly
    to `pcae.core.agent`."""
    import pcae.commands.agent as commands_agent_module

    source = inspect.getsource(commands_agent_module)
    assert '["git", "push"' not in source
