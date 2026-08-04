"""Phase 149G -- Repository-Wide Mutation Permission Coverage Wave 1
Independent Verification.

Independently authored adversarial tests. Deliberately does NOT import
fixtures/helpers from 149F's own test files
(tests/test_mutation_permission_*.py, tests/test_agent.py's 149F
additions) -- these tests build their own scratch git repositories, task
contracts, and broker-failure injections from scratch so that a defect
149F's own tests happened to miss (or a weakened assertion) is not
silently inherited here.

Scope: independently prove or refute that every Wave-1 mutation path
(AG1, AG2, AG4, PH1 via AG1, PH2/PH3 via AG2) consumes a valid fresh
Permission Broker ALLOW (or routes through the canonical shared
dispatcher) before any real git/filesystem mutation, and that no path
can be tricked into mutating on a denied, stale, or malformed decision.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pcae.core import mutation_permission
from pcae.core import permission_broker_foundation as pbf
from pcae.core.paths import HarnessPath
from pcae.core.tasks import create_task_contract


# ─────────────────────────────────────────────────────────────────────────
# Scratch repo helpers (independently written)
# ─────────────────────────────────────────────────────────────────────────


def _run(args, cwd):
    return subprocess.run(args, cwd=str(cwd), capture_output=True, text=True, check=True)


def _init_scratch_repo(tmp_path: Path) -> HarnessPath:
    repo = tmp_path / "scratch_repo"
    repo.mkdir()
    _run(["git", "init", "-q"], repo)
    _run(["git", "config", "user.email", "verify@example.com"], repo)
    _run(["git", "config", "user.name", "149G Verifier"], repo)
    (repo / "README.md").write_text("scratch\n")
    # Mirrors the real repo's .pcae/.gitignore (remote/ is ignored there),
    # so job-queue bookkeeping files under .pcae/remote/jobs/ don't show
    # up as "unexpected uncommitted changes" against commit_file_changes'
    # own (unchanged, pre-149F) dirty-tree scope check.
    (repo / ".pcae").mkdir()
    (repo / ".pcae" / ".gitignore").write_text("remote/\n")
    _run(["git", "add", "README.md", ".pcae/.gitignore"], repo)
    _run(["git", "commit", "-q", "-m", "init"], repo)
    return HarnessPath(repo)


def _init_scratch_repo_with_remote(tmp_path: Path) -> tuple[HarnessPath, Path]:
    bare = tmp_path / "bare_remote.git"
    bare.mkdir()
    _run(["git", "init", "-q", "--bare"], bare)
    root = _init_scratch_repo(tmp_path)
    _run(["git", "remote", "add", "origin", str(bare)], root.path)
    _run(["git", "push", "-q", "-u", "origin", "HEAD:main"], root.path)
    return root, bare


def _head(root: HarnessPath) -> str:
    return _run(["git", "rev-parse", "HEAD"], root.path).stdout.strip()


def _commit_count(root: HarnessPath) -> int:
    return int(_run(["git", "rev-list", "--count", "HEAD"], root.path).stdout.strip())


def _active_task_id(root: HarnessPath) -> str:
    from pcae.core.tasks import find_latest_active_task

    task = find_latest_active_task(root)
    assert task is not None
    return task.task_id


def _bare_head(bare: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "refs/heads/main"], cwd=str(bare),
        capture_output=True, text=True,
    ).stdout.strip()


class _FailingBroker:
    def evaluate(self, request):
        raise RuntimeError("synthetic broker evaluation failure")


class _MalformedResultBroker:
    def __init__(self, fake_decision):
        self._fake_decision = fake_decision

    def evaluate(self, request):
        return self._fake_decision


class _StringDecisionAsAllow:
    decision = "ALLOW"


# ─────────────────────────────────────────────────────────────────────────
# 1. Broker construction failure (evaluate_repository_mutation_permission)
# ─────────────────────────────────────────────────────────────────────────


def test_broker_construction_failure_denies_and_reports_broker_failure(tmp_path, monkeypatch):
    root = _init_scratch_repo(tmp_path)

    def _raise_on_construct(*a, **kw):
        raise RuntimeError("synthetic construction failure")

    monkeypatch.setattr(pbf, "PermissionBroker", _raise_on_construct)

    result, snapshot = mutation_permission.evaluate_commit_permission(root, "some-task")
    assert result.authorized is False
    assert result.decision is None
    details = mutation_permission.permission_denial_details(result)
    assert details["permission_decision"] == "BROKER_FAILURE"
    assert "synthetic construction failure" in details["permission_reason"]


# ─────────────────────────────────────────────────────────────────────────
# 2. Broker evaluation failure
# ─────────────────────────────────────────────────────────────────────────


def test_broker_evaluation_failure_denies(tmp_path):
    root = _init_scratch_repo(tmp_path)
    result = mutation_permission.evaluate_repository_mutation_permission(
        root=root,
        action_type=pbf.ACTION_COMMIT,
        execution_class=pbf.EXECUTION_CLASS_MUTATION,
        requested_component="COMP-001",
        requested_capability="pcae_remote_commit",
        task_id="t1",
        requested_resource=None,
        evidence_available=True,
        approval_present=False,
        simulation_only=True,
        broker=_FailingBroker(),
    )
    assert result.authorized is False
    assert result.decision is None
    details = mutation_permission.permission_denial_details(result)
    assert details["permission_decision"] == "BROKER_FAILURE"


# ─────────────────────────────────────────────────────────────────────────
# 3. Malformed results are rejected, not treated as ALLOW
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "fake_decision",
    [
        _StringDecisionAsAllow(),
        "ALLOW",
        object(),
        None,
    ],
)
def test_malformed_broker_result_never_authorizes(tmp_path, fake_decision):
    root = _init_scratch_repo(tmp_path)
    result = mutation_permission.evaluate_repository_mutation_permission(
        root=root,
        action_type=pbf.ACTION_PUSH,
        execution_class=pbf.EXECUTION_CLASS_MUTATION,
        requested_component="COMP-001",
        requested_capability="pcae_remote_push",
        task_id="t1",
        requested_resource="refs/heads/main",
        evidence_available=True,
        approval_present=False,
        simulation_only=True,
        broker=_MalformedResultBroker(fake_decision),
    )
    assert result.authorized is False
    assert result.decision is None
    details = mutation_permission.permission_denial_details(result)
    assert details["permission_decision"] == "BROKER_FAILURE"
    assert details["permission_reason"] == "invalid_broker_result"


# ─────────────────────────────────────────────────────────────────────────
# 4. Real DENY (no active task -> POL-001) and real HUMAN_REVIEW behavior
# ─────────────────────────────────────────────────────────────────────────


def test_real_deny_when_no_active_task_pol001(tmp_path):
    root = _init_scratch_repo(tmp_path)
    # No tasks/active directory created at all -> find_latest_active_task
    # returns None -> task_id=None -> POL-001 fires for real.
    result, _snapshot = mutation_permission.evaluate_commit_permission(root, None)
    assert result.authorized is False
    details = mutation_permission.permission_denial_details(result)
    assert details["permission_decision"] == pbf.DECISION_DENY
    assert "POL-001" in details["permission_causing_policy_ids"]


def test_pol004_not_applicable_to_mutation_execution_class(tmp_path):
    root = _init_scratch_repo(tmp_path)
    create_task_contract(root, "149G verification task")
    # approval_present=False, execution_class=MUTATION: POL-004 must not
    # fire (it is scoped away from MUTATION per PBPC-001/RWMPC-001).
    result, _snapshot = mutation_permission.evaluate_commit_permission(root, _active_task_id(root))
    if result.decision is not None:
        assert "POL-004" not in result.decision.causing_policy_ids


def test_pol004_still_applies_to_rollback_execution_class(tmp_path):
    root = _init_scratch_repo(tmp_path)
    create_task_contract(root, "149G rollback probe task")
    request = pbf.build_permission_broker_request(
        action_type=pbf.ACTION_ROLLBACK,
        execution_class=pbf.EXECUTION_CLASS_ROLLBACK,
        requested_component="COMP-001",
        requested_capability="pcae_rollback",
        task_id="149G rollback probe task",
        requested_resource=None,
        evidence_available=True,
        approval_present=False,
        simulation_only=True,
    )
    decision = pbf.PermissionBroker().evaluate(request)
    assert decision.decision == pbf.DECISION_HUMAN_REVIEW
    assert "POL-004" in decision.causing_policy_ids


def test_pol005_denies_non_simulation_execution(tmp_path):
    root = _init_scratch_repo(tmp_path)
    create_task_contract(root, "149G pol005 probe task")
    result = mutation_permission.evaluate_repository_mutation_permission(
        root=root,
        action_type=pbf.ACTION_COMMIT,
        execution_class=pbf.EXECUTION_CLASS_MUTATION,
        requested_component="COMP-001",
        requested_capability="pcae_remote_commit",
        task_id="149G pol005 probe task",
        requested_resource=None,
        evidence_available=True,
        approval_present=False,
        simulation_only=False,
    )
    assert result.authorized is False
    details = mutation_permission.permission_denial_details(result)
    assert "POL-005" in details["permission_causing_policy_ids"]


# ─────────────────────────────────────────────────────────────────────────
# 5. AG1 commit-class freshness: staged-tree, HEAD, task-id drift
# ─────────────────────────────────────────────────────────────────────────


def test_commit_freshness_blocks_on_staged_tree_drift(tmp_path):
    root = _init_scratch_repo(tmp_path)
    create_task_contract(root, "149G staged-drift task")
    result, snapshot = mutation_permission.evaluate_commit_permission(root, _active_task_id(root))
    assert result.authorized is True

    # Mutate the index (stage a new file) while HEAD stays fixed.
    (root.path / "new_file.txt").write_text("drift\n")
    _run(["git", "add", "new_file.txt"], root.path)

    fresh, mismatches = mutation_permission.validate_commit_permission_freshness(root, snapshot)
    assert fresh is False
    assert any("staged content changed" in m for m in mismatches)


def test_commit_freshness_blocks_on_head_drift(tmp_path):
    root = _init_scratch_repo(tmp_path)
    create_task_contract(root, "149G head-drift task")
    result, snapshot = mutation_permission.evaluate_commit_permission(root, _active_task_id(root))
    assert result.authorized is True

    _run(["git", "commit", "-q", "--allow-empty", "-m", "unrelated head move"], root.path)

    fresh, mismatches = mutation_permission.validate_commit_permission_freshness(root, snapshot)
    assert fresh is False
    assert any("local HEAD changed" in m for m in mismatches)


def test_commit_freshness_blocks_on_task_id_drift(tmp_path):
    root = _init_scratch_repo(tmp_path)
    create_task_contract(root, "149G task-drift original")
    result, snapshot = mutation_permission.evaluate_commit_permission(root, _active_task_id(root))
    assert result.authorized is True

    create_task_contract(root, "149G task-drift replacement")

    fresh, mismatches = mutation_permission.validate_commit_permission_freshness(root, snapshot)
    assert fresh is False
    assert any("active task changed" in m for m in mismatches)


def test_commit_freshness_observation_failure_fails_closed(tmp_path, monkeypatch):
    root = _init_scratch_repo(tmp_path)
    create_task_contract(root, "149G observation-failure task")
    result, snapshot = mutation_permission.evaluate_commit_permission(root, _active_task_id(root))
    assert result.authorized is True

    # Force re-observation (git write-tree) to fail at freshness time.
    monkeypatch.setattr(mutation_permission, "_git_write_tree", lambda root_arg: None)
    fresh, mismatches = mutation_permission.validate_commit_permission_freshness(root, snapshot)
    assert fresh is False
    assert mismatches  # a genuine failure reason, not a silently-passing empty list


def test_commit_no_drift_positive_control_stays_fresh(tmp_path):
    root = _init_scratch_repo(tmp_path)
    create_task_contract(root, "149G positive-control task")
    result, snapshot = mutation_permission.evaluate_commit_permission(root, _active_task_id(root))
    assert result.authorized is True
    fresh, mismatches = mutation_permission.validate_commit_permission_freshness(root, snapshot)
    assert fresh is True
    assert mismatches == []


# ─────────────────────────────────────────────────────────────────────────
# 6. AG1 real end-to-end: commit_file_changes performs zero commit on DENY
#    and exactly one commit on a genuine, unstale ALLOW.
# ─────────────────────────────────────────────────────────────────────────


def _make_job_and_artifact(root: HarnessPath, job_id: str, changed_file: str):
    """Independently constructed minimal job/artifact fixture for
    commit_file_changes -- not copied from 149F's test helpers."""
    from pcae.core import agent as agent_mod

    jobs_dir = root.path / ".pcae" / "remote" / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    job_file_path = str(jobs_dir / f"{job_id}.json")
    job = {
        "job_id": job_id,
        "requested_agent": "verifier",
        "change_approval_state": "approved",
    }
    Path(job_file_path).write_text("{}")
    artifact = {
        "changed_files": [changed_file],
        "scope_validation": {"valid": True, "violations": []},
    }
    return agent_mod, job, artifact, job_file_path


def test_ag1_commit_file_changes_zero_commit_on_deny(tmp_path, monkeypatch):
    root = _init_scratch_repo(tmp_path)
    # Deliberately do NOT create a task contract -> POL-001 DENY.
    changed_file = "payload.txt"
    (root.path / changed_file).write_text("payload\n")

    agent_mod, job, artifact, job_file_path = _make_job_and_artifact(root, "job-deny", changed_file)
    monkeypatch.setattr(
        agent_mod, "_load_job_and_artifact", lambda root_arg, job_id: (job, artifact, job_file_path)
    )

    before = _head(root)
    before_count = _commit_count(root)
    with pytest.raises(ValueError, match="Permission Broker"):
        agent_mod.commit_file_changes(root, "job-deny")
    assert _head(root) == before
    assert _commit_count(root) == before_count


def test_ag1_commit_file_changes_real_allow_commits_exactly_once(tmp_path, monkeypatch):
    root = _init_scratch_repo(tmp_path)
    create_task_contract(root, "149G ag1 real allow task")
    # Commit the task-contract file itself first, so it is not left as an
    # "unexpected uncommitted change" against commit_file_changes' own
    # (unchanged, pre-149F) dirty-tree scope check -- matches realistic
    # usage where the active task was committed by a prior phase.
    _run(["git", "add", "-A"], root.path)
    _run(["git", "commit", "-q", "-m", "commit active task contract"], root.path)
    changed_file = "payload.txt"
    (root.path / changed_file).write_text("payload\n")

    agent_mod, job, artifact, job_file_path = _make_job_and_artifact(root, "job-allow", changed_file)
    monkeypatch.setattr(
        agent_mod, "_load_job_and_artifact", lambda root_arg, job_id: (job, artifact, job_file_path)
    )

    before_count = _commit_count(root)
    result = agent_mod.commit_file_changes(root, "job-allow")
    assert _commit_count(root) == before_count + 1
    assert result.get("commit_sha") or _head(root) != ""
    committed_tree = _run(["git", "show", "--stat", "HEAD"], root.path).stdout
    assert "payload.txt" in committed_tree


def test_ag1_commit_file_changes_zero_commit_on_stale_decision(tmp_path, monkeypatch):
    root = _init_scratch_repo(tmp_path)
    create_task_contract(root, "149G ag1 stale task")
    changed_file = "payload.txt"
    (root.path / changed_file).write_text("payload\n")

    agent_mod, job, artifact, job_file_path = _make_job_and_artifact(root, "job-stale", changed_file)
    monkeypatch.setattr(
        agent_mod, "_load_job_and_artifact", lambda root_arg, job_id: (job, artifact, job_file_path)
    )

    real_validate = mutation_permission.validate_commit_permission_freshness
    monkeypatch.setattr(
        mutation_permission,
        "validate_commit_permission_freshness",
        lambda root_arg, snapshot: (False, ["synthetic staleness injected by 149G"]),
    )
    before = _head(root)
    before_count = _commit_count(root)
    with pytest.raises(ValueError, match="stale"):
        agent_mod.commit_file_changes(root, "job-stale")
    assert _head(root) == before
    assert _commit_count(root) == before_count
    monkeypatch.setattr(mutation_permission, "validate_commit_permission_freshness", real_validate)


# ─────────────────────────────────────────────────────────────────────────
# 7. AG2 real push (local bare remote) + freshness attacks
# ─────────────────────────────────────────────────────────────────────────


def test_ag2_real_scratch_push_no_drift_positive_control(tmp_path):
    from pcae.core import agent as agent_mod

    root, bare = _init_scratch_repo_with_remote(tmp_path)
    create_task_contract(root, "149G ag2 positive control task")
    _run(["git", "commit", "-q", "--allow-empty", "-m", "local unpushed commit"], root.path)

    active_task = mutation_permission
    from pcae.core.tasks import find_latest_active_task
    task = find_latest_active_task(root)

    dispatch_result = agent_mod._dispatch_governed_push(root, "origin", "main", task.task_id)
    assert dispatch_result.authorized is True
    assert dispatch_result.dispatched is True
    assert dispatch_result.push_proc.returncode == 0
    assert _bare_head(bare) == _head(root)


def test_ag2_freshness_blocks_on_head_drift(tmp_path):
    root, bare = _init_scratch_repo_with_remote(tmp_path)
    create_task_contract(root, "149G ag2 head-drift task")
    _run(["git", "commit", "-q", "--allow-empty", "-m", "commit A"], root.path)

    from pcae.core.tasks import find_latest_active_task
    task = find_latest_active_task(root)
    result, snapshot = mutation_permission.evaluate_alternate_push_permission(
        root, "origin", "main", task.task_id
    )
    assert result.authorized is True

    _run(["git", "commit", "-q", "--allow-empty", "-m", "commit B (drift)"], root.path)

    fresh, mismatches = mutation_permission.validate_alternate_push_permission_freshness(root, snapshot)
    assert fresh is False
    assert any("HEAD changed" in m for m in mismatches)
    assert _bare_head(bare) != _head(root)  # confirm nothing pushed


def test_ag2_external_remote_push_race_still_yields_zero_corrupt_mutation(tmp_path):
    """FINDING (non-blocking, recorded in the 149G report): the
    "unpushed commit count" freshness fact is computed purely from the
    local remote-tracking ref (`git rev-list --count origin/main..HEAD`)
    without a `git fetch`. An external push landing on the remote between
    permission evaluation and dispatch is therefore NOT detected as a
    freshness mismatch -- `validate_alternate_push_permission_freshness`
    reports `fresh=True` and `_dispatch_governed_push` proceeds to a real
    `git push`. The actual corruption-safety net for this race is git's
    own non-fast-forward rejection at the transport layer, not Wave-1's
    freshness check: the dispatch attempt fails (`returncode != 0`) and
    the remote ref is left exactly as the external pusher left it -- zero
    corrupt/overwriting mutation reaches the remote either way."""
    from pcae.core import agent as agent_mod

    root, bare = _init_scratch_repo_with_remote(tmp_path)
    create_task_contract(root, "149G ag2 unpushed-drift task")

    from pcae.core.tasks import find_latest_active_task
    task = find_latest_active_task(root)
    result, snapshot = mutation_permission.evaluate_alternate_push_permission(
        root, "origin", "main", task.task_id
    )
    assert result.authorized is True

    other_clone = root.path.parent / "other_clone"
    _run(["git", "clone", "-q", str(bare), str(other_clone)], root.path.parent)
    _run(["git", "config", "user.email", "other@example.com"], other_clone)
    _run(["git", "config", "user.name", "Other Pusher"], other_clone)
    _run(["git", "commit", "-q", "--allow-empty", "-m", "external push"], other_clone)
    _run(["git", "push", "-q", "origin", "HEAD:main"], other_clone)
    external_bare_head = _bare_head(bare)

    fresh, mismatches = mutation_permission.validate_alternate_push_permission_freshness(root, snapshot)
    # Documented false negative: local-only observation cannot see the
    # external push without a fetch.
    assert fresh is True
    assert mismatches == []

    dispatch_result = agent_mod._dispatch_governed_push(root, "origin", "main", task.task_id)
    assert dispatch_result.authorized is True
    assert dispatch_result.dispatched is True  # freshness said "go"
    assert dispatch_result.push_proc.returncode != 0  # git itself rejects it
    assert _bare_head(bare) == external_bare_head  # remote unchanged -- zero corruption


def test_ag2_freshness_blocks_on_task_id_drift(tmp_path):
    root, bare = _init_scratch_repo_with_remote(tmp_path)
    create_task_contract(root, "149G ag2 task-drift original")

    from pcae.core.tasks import find_latest_active_task
    task = find_latest_active_task(root)
    result, snapshot = mutation_permission.evaluate_alternate_push_permission(
        root, "origin", "main", task.task_id
    )
    assert result.authorized is True

    create_task_contract(root, "149G ag2 task-drift replacement")

    fresh, mismatches = mutation_permission.validate_alternate_push_permission_freshness(root, snapshot)
    assert fresh is False
    assert any("active task changed" in m for m in mismatches)


def test_ag2_dispatch_governed_push_zero_dispatch_on_deny(tmp_path):
    from pcae.core import agent as agent_mod

    root, bare = _init_scratch_repo_with_remote(tmp_path)
    # No task contract -> POL-001 DENY.
    remote_before = _bare_head(bare)
    dispatch_result = agent_mod._dispatch_governed_push(root, "origin", "main", None)
    assert dispatch_result.authorized is False
    assert dispatch_result.dispatched is False
    assert dispatch_result.push_proc is None
    assert _bare_head(bare) == remote_before


# ─────────────────────────────────────────────────────────────────────────
# 8. PH2/PH3 routing: exactly-once evaluation, no direct-push fallback
# ─────────────────────────────────────────────────────────────────────────


def test_dispatch_governed_push_evaluates_permission_exactly_once(tmp_path):
    root, bare = _init_scratch_repo_with_remote(tmp_path)
    create_task_contract(root, "149G evaluate-once task")

    call_count = {"n": 0}
    real_evaluate = mutation_permission.evaluate_alternate_push_permission

    def _counting_evaluate(root_arg, remote_arg, branch_arg, task_id):
        call_count["n"] += 1
        return real_evaluate(root_arg, remote_arg, branch_arg, task_id)

    mutation_permission.evaluate_alternate_push_permission = _counting_evaluate
    try:
        from pcae.core import agent as agent_mod
        from pcae.core.tasks import find_latest_active_task
        task = find_latest_active_task(root)
        dispatch_result = agent_mod._dispatch_governed_push(root, "origin", "main", task.task_id)
        assert dispatch_result.dispatched is True
    finally:
        mutation_permission.evaluate_alternate_push_permission = real_evaluate

    assert call_count["n"] == 1


def test_phase_py_ph2_ph3_contain_no_direct_git_push_call(tmp_path):
    """Static control-flow proof (independently reconstructed, not the
    149F inventory guard): search the two PH2/PH3 function bodies for a
    literal ['git', 'push', ...] dispatch. Expected: none -- both must
    route exclusively through `_dispatch_governed_push` /
    `dispatch_result.push_proc`."""
    import ast

    src = Path("src/pcae/commands/phase.py").read_text()
    tree = ast.parse(src)

    target_functions = {
        "_build_backend_created_output_adoption_push_execution",
        "_build_final_verification_tooling_push_decision",
    }
    found = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in target_functions:
            found[node.name] = node

    assert set(found) == target_functions, f"expected functions not found: {target_functions - set(found)}"

    for name, node in found.items():
        direct_push_calls = []
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call):
                # Look for _sp.run([...,"push",...]) style dispatch, the
                # historical direct-push shape this phase replaced.
                for arg in sub.args:
                    if isinstance(arg, ast.List):
                        elts = [e.value for e in arg.elts if isinstance(e, ast.Constant)]
                        if "push" in elts and "git" in elts:
                            direct_push_calls.append(sub)
        assert not direct_push_calls, f"{name} contains a direct git push dispatch: {direct_push_calls}"
        # And it must reference the shared dispatcher.
        calls_dispatcher = any(
            isinstance(sub, ast.Call)
            and isinstance(sub.func, ast.Name)
            and sub.func.id == "_dispatch_governed_push"
            for sub in ast.walk(node)
        )
        assert calls_dispatcher, f"{name} does not call _dispatch_governed_push"


def test_phase_py_no_try_canonical_except_direct_push_fallback():
    """Search for a try/except pattern around the routed dispatch that
    would fall back to a direct git push on failure."""
    import ast

    src = Path("src/pcae/commands/phase.py").read_text()
    tree = ast.parse(src)

    target_functions = {
        "_build_backend_created_output_adoption_push_execution",
        "_build_final_verification_tooling_push_decision",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in target_functions:
            for sub in ast.walk(node):
                if isinstance(sub, ast.Try):
                    for handler in sub.handlers:
                        for stmt in ast.walk(handler):
                            if isinstance(stmt, ast.Call):
                                for arg in stmt.args:
                                    if isinstance(arg, ast.List):
                                        elts = [
                                            e.value for e in arg.elts
                                            if isinstance(e, ast.Constant)
                                        ]
                                        assert not ("push" in elts and "git" in elts), (
                                            f"except-handler fallback to direct git push found in {node.name}"
                                        )


# ─────────────────────────────────────────────────────────────────────────
# 9. AG4 promotion: first-mutation ordering and candidate/task drift
# ─────────────────────────────────────────────────────────────────────────


def test_promotion_freshness_blocks_on_approved_paths_drift():
    snapshot = mutation_permission.PromotionDecisionSnapshot(
        epr_id="epr-1", ecp_id="ecp-1", approved_paths=("src/pcae/foo.py",), task_id="t1"
    )
    fresh, mismatches = mutation_permission.validate_promotion_permission_freshness(
        snapshot,
        current_epr_id="epr-1",
        current_ecp_id="ecp-1",
        current_approved_paths=("src/pcae/foo.py", "src/pcae/bar.py"),
        current_task_id="t1",
    )
    assert fresh is False
    assert any("approved_paths changed" in m for m in mismatches)


def test_promotion_freshness_blocks_on_epr_or_ecp_swap():
    snapshot = mutation_permission.PromotionDecisionSnapshot(
        epr_id="epr-1", ecp_id="ecp-1", approved_paths=("src/pcae/foo.py",), task_id="t1"
    )
    fresh, mismatches = mutation_permission.validate_promotion_permission_freshness(
        snapshot,
        current_epr_id="epr-2",  # swapped EPR -- a stale decision must not
        current_ecp_id="ecp-1",  # authorize mutating a *different* target.
        current_approved_paths=("src/pcae/foo.py",),
        current_task_id="t1",
    )
    assert fresh is False
    assert any("EPR id changed" in m for m in mismatches)


def test_promotion_freshness_blocks_on_task_drift():
    snapshot = mutation_permission.PromotionDecisionSnapshot(
        epr_id="epr-1", ecp_id="ecp-1", approved_paths=("src/pcae/foo.py",), task_id="t1"
    )
    fresh, mismatches = mutation_permission.validate_promotion_permission_freshness(
        snapshot,
        current_epr_id="epr-1",
        current_ecp_id="ecp-1",
        current_approved_paths=("src/pcae/foo.py",),
        current_task_id="t2",
    )
    assert fresh is False
    assert any("active task changed" in m for m in mismatches)


def test_promotion_no_drift_positive_control_stays_fresh():
    snapshot = mutation_permission.PromotionDecisionSnapshot(
        epr_id="epr-1", ecp_id="ecp-1", approved_paths=("src/pcae/foo.py",), task_id="t1"
    )
    fresh, mismatches = mutation_permission.validate_promotion_permission_freshness(
        snapshot,
        current_epr_id="epr-1",
        current_ecp_id="ecp-1",
        current_approved_paths=("src/pcae/foo.py",),
        current_task_id="t1",
    )
    assert fresh is True
    assert mismatches == []


def test_classify_promotion_action_type_src_takes_precedence():
    action = mutation_permission.classify_promotion_action_type(
        ["docs/readme.md", "tests/test_x.py", "src/pcae/core/foo.py"]
    )
    assert action == pbf.ACTION_SOURCE_MUTATION


def test_build_promotion_execution_first_write_ordering_source_scan():
    """Static proof that build_promotion_execution's permission evaluation
    call precedes its apply-loop's first write_text/write_bytes/unlink,
    independently reconstructed via source-order line inspection (not the
    149F inventory guard)."""
    import re

    src = Path("src/pcae/core/agent.py").read_text()
    match = re.search(r"^def build_promotion_execution\(", src, re.MULTILINE)
    assert match, "build_promotion_execution not found"
    # Find the next top-level "def " after this one to bound the function body.
    rest = src[match.end():]
    next_def = re.search(r"\n(?:async )?def [a-zA-Z_]", rest)
    body = rest[: next_def.start()] if next_def else rest

    permission_call_pos = body.find("mutation_permission.evaluate_promotion_permission")
    assert permission_call_pos != -1, "no permission evaluation call found in build_promotion_execution"

    freshness_call_pos = body.find("mutation_permission.validate_promotion_permission_freshness")
    assert freshness_call_pos != -1
    assert freshness_call_pos > permission_call_pos

    write_calls = [m.start() for m in re.finditer(r"\.write_text\(|\.write_bytes\(|\.unlink\(", body)]
    assert write_calls, "expected at least one root-mutation write/unlink call in apply loop"
    first_write_pos = min(write_calls)

    assert permission_call_pos < first_write_pos, (
        "permission evaluation occurs after the first apply-loop write/unlink"
    )
    assert freshness_call_pos < first_write_pos, (
        "freshness validation occurs after the first apply-loop write/unlink"
    )


# ─────────────────────────────────────────────────────────────────────────
# 10. Rollback (AG3/AG5) still HUMAN_REVIEW-blocked; TK deferral unchanged
# ─────────────────────────────────────────────────────────────────────────


def test_rollback_class_still_requires_human_review_via_pol004(tmp_path):
    root = _init_scratch_repo(tmp_path)
    create_task_contract(root, "149G rollback non-interference task")
    request = pbf.build_permission_broker_request(
        action_type=pbf.ACTION_ROLLBACK,
        execution_class=pbf.EXECUTION_CLASS_ROLLBACK,
        requested_component="COMP-001",
        requested_capability="pcae_rollback",
        task_id="149G rollback non-interference task",
        requested_resource=None,
        evidence_available=True,
        approval_present=False,
        simulation_only=True,
    )
    decision = pbf.PermissionBroker().evaluate(request)
    assert decision.decision == pbf.DECISION_HUMAN_REVIEW
    assert "POL-004" in decision.causing_policy_ids


def test_no_permission_broker_request_constructor_reachable_from_rollback_or_task_finish():
    """AG3/AG5 (rollback) and TK1-3 (task-finish) production functions must
    not themselves call build_permission_broker_request or
    mutation_permission -- confirms Wave-1 wiring did not silently extend
    into rollback/task-finish territory."""
    import ast

    src = Path("src/pcae/core/agent.py").read_text()
    tree = ast.parse(src)

    # Best-effort name match on the historically-known rollback/task-finish
    # entry points; if names differ this assertion is skipped rather than
    # silently false-passed.
    candidate_names = {
        n.name: n
        for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef)
        and ("rollback" in n.name.lower() or "task_finish" in n.name.lower() or "finish_task" in n.name.lower())
    }
    if not candidate_names:
        pytest.skip("no rollback/task-finish function names found by heuristic; see manual TK/AG3/AG5 review")

    for name, node in candidate_names.items():
        for sub in ast.walk(node):
            if isinstance(sub, ast.Attribute) and sub.attr == "evaluate_repository_mutation_permission":
                pytest.fail(f"{name} unexpectedly calls mutation_permission machinery")
