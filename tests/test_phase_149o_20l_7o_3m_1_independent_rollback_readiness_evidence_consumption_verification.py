"""Independent Phase 149O.20L.7O.3M.1 rollback-evidence verification.

This suite is intentionally independent of the Phase 3M tests.  It executes
the fixed pre-3M tree (7b193145) in a separate interpreter, constructs fresh
PER/ECP fixtures directly, and compares that behavior with the current tree.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from pcae.cli import main
from pcae.core import agent
from pcae.core import hatp_mandatory_cutover as cutover
from pcae.core import mutation_permission
from pcae.core import permission_broker_foundation as pbf
from pcae.core.hatp_mandatory_cutover import CutoverMode, CutoverModeResolution
from pcae.core.paths import HarnessPath
from pcae.core.tasks import create_task_contract


pytestmark = pytest.mark.fast_green

PRE_3M_COMMIT = "7b19314591c2f954b727a3a96746747e38a55bb1"
INTEGRATION_COMMIT = "e632a2dfee77b8f83e03af1a34ad78aa7136c447"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fixed_mode(mode: CutoverMode) -> CutoverModeResolution:
    return CutoverModeResolution(mode, f"3m1-fixed-{mode.value}")


def _setup(
    base: Path,
    *,
    per_id: str = "per-3m1",
    path: str = "promoted.txt",
    current: bytes = b"promoted\n",
    before: bytes | None = None,
) -> tuple[HarnessPath, Path]:
    base.mkdir(parents=True, exist_ok=True)
    create_task_contract(HarnessPath(base), "3M.1 independent rollback fixture")
    target = base / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(current)
    root = HarnessPath(base)
    entry = {
        "path": path,
        "change_type": "added" if before is None else "modified",
        "before_hash": None if before is None else _sha(before),
        "after_hash": _sha(current),
        "content": current.decode(),
        "binary": False,
        "promotion_eligible": True,
        "before_content": None if before is None else before.decode(),
        "before_exists": before is not None,
    }
    ecp = {
        "ecp_id": "ecp-3m1",
        "ecp_version": "1.0",
        "prompt_id": "prompt-3m1",
        "authorization_id": "auth-3m1",
        "audit_id": "audit-3m1",
        "snapshot_id": "snapshot-3m1",
        "change_record_id": None,
        "execution_result_id": "result-3m1",
        "captured_at": "2026-08-26T00:00:00+00:00",
        "capture_source": "sandbox_dir",
        "capture_outcome": "success",
        "sandbox_id": "sandbox-3m1",
        "sandbox_provider": "git_worktree",
        "pre_git_head": "baseline",
        "post_git_head": "baseline",
        "git_head_diverged": False,
        "git_commit_detected": False,
        "manifest_hash": None,
        "file_count": 1,
        "file_entries": [entry],
        "capture_errors": [],
        "binary_file_count": 0,
        "symlink_count": 0,
        "external_symlink_count": 0,
        "excluded_file_count": 0,
        "excluded_paths": [],
        "absolute_path_writes_detected": False,
        "promotion_eligible_count": 1,
        "esa_available": True,
        "execution_allowed": False,
        "promotion_executed": False,
        "rollback_executed": False,
    }
    per = {
        "per_id": per_id,
        "per_version": "1.0",
        "epr_id": "epr-3m1",
        "ecp_id": ecp["ecp_id"],
        "prompt_id": ecp["prompt_id"],
        "started_at": "2026-08-26T00:00:00+00:00",
        "divergence_check": {},
        "file_plan": [path],
        "file_results": [{"path": path, "outcome": "success"}],
        "status": "completed",
        "completed_at": "2026-08-26T00:00:01+00:00",
        "promotion_executed": True,
        "rollback_payload_available": True,
        "execution_allowed": False,
        "rollback_executed": False,
    }
    assert agent.store_execution_change_package(root, ecp)["stored"] is True
    assert agent.store_promotion_execution_record(root, per)["stored"] is True
    return root, target


@pytest.fixture(scope="session")
def pre_3m_tree(tmp_path_factory: pytest.TempPathFactory) -> Path:
    tree = tmp_path_factory.mktemp("pre-3m-tree")
    archive = subprocess.run(
        ["git", "archive", PRE_3M_COMMIT],
        cwd=Path(__file__).resolve().parents[1],
        check=True,
        stdout=subprocess.PIPE,
    )
    subprocess.run(["tar", "-x", "-C", str(tree)], input=archive.stdout, check=True)
    return tree


_BASELINE_DRIVER = r'''
import hashlib, json, pathlib, sys
from pcae.core import agent
from pcae.core.paths import HarnessPath
from pcae.core.tasks import create_task_contract

root_path = pathlib.Path(sys.argv[1])
scenario = sys.argv[2]
root_path.mkdir(parents=True, exist_ok=True)
create_task_contract(HarnessPath(root_path), "3M.1 pre-3M fixture")
target = root_path / "promoted.txt"
target.write_text("promoted\n")
after_hash = hashlib.sha256(b"promoted\n").hexdigest()
ecp = {
  "ecp_id":"ecp-3m1", "ecp_version":"1.0", "prompt_id":"prompt-3m1",
  "authorization_id":"auth", "audit_id":"audit", "snapshot_id":"snap",
  "change_record_id":None, "execution_result_id":"result",
  "captured_at":"2026-08-26T00:00:00+00:00", "capture_source":"sandbox_dir",
  "capture_outcome":"success", "sandbox_id":"sandbox", "sandbox_provider":"git_worktree",
  "pre_git_head":"baseline", "post_git_head":"baseline", "git_head_diverged":False,
  "git_commit_detected":False, "manifest_hash":None, "file_count":1,
  "file_entries":[{"path":"promoted.txt", "change_type":"added", "before_hash":None,
    "after_hash":after_hash, "content":"promoted\n", "binary":False,
    "promotion_eligible":True, "before_content":None, "before_exists":False}],
  "capture_errors":[], "binary_file_count":0, "symlink_count":0,
  "external_symlink_count":0, "excluded_file_count":0, "excluded_paths":[],
  "absolute_path_writes_detected":False, "promotion_eligible_count":1,
  "esa_available":True, "execution_allowed":False, "promotion_executed":False,
  "rollback_executed":False}
per = {"per_id":"per-3m1", "per_version":"1.0", "epr_id":"epr-3m1",
  "ecp_id":"ecp-3m1", "prompt_id":"prompt-3m1",
  "started_at":"2026-08-26T00:00:00+00:00", "divergence_check":{},
  "file_plan":["promoted.txt"],
  "file_results":[{"path":"promoted.txt", "outcome":"success"}],
  "status":"completed", "completed_at":"2026-08-26T00:00:01+00:00",
  "promotion_executed":True, "rollback_payload_available":True,
  "execution_allowed":False, "rollback_executed":False}
root = HarnessPath(root_path)
assert agent.store_execution_change_package(root, ecp)["stored"]
assert agent.store_promotion_execution_record(root, per)["stored"]
if scenario == "divergence": target.write_text("external change\n")
result = agent.build_rollback_execution(root, "per-3m1", dry_run=scenario == "dry")
record = agent.lookup_rollback_execution_record(root, result.get("rer_id", ""))
print(json.dumps({"result": result, "record": record, "target_exists": target.exists()}))
'''


def _baseline(pre_3m_tree: Path, root: Path, scenario: str) -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(pre_3m_tree / "src")
    proc = subprocess.run(
        [sys.executable, "-c", _BASELINE_DRIVER, str(root), scenario],
        cwd=root.parent,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def _deny(monkeypatch: pytest.MonkeyPatch) -> dict[str, int]:
    calls = {"count": 0}

    def evaluate(_self, _request):
        calls["count"] += 1
        return pbf.PermissionBrokerDecision(
            decision=pbf.DECISION_DENY,
            decision_reason="3m1_forced_deny",
            matched_no_go_ids=(),
            matched_invariants=(),
            required_remediation=(),
            requires_human=False,
            simulation_only=True,
        )

    monkeypatch.setattr(pbf.PermissionBroker, "evaluate", evaluate)
    return calls


def _add_second_path(root: HarnessPath, *, path: str = "second.txt") -> Path:
    target = root.path / path
    target.write_text("second promoted\n")
    ecp = agent.lookup_execution_change_package(root, "ecp-3m1")
    per = agent.lookup_promotion_execution_record(root, "per-3m1")
    assert ecp is not None and per is not None
    ecp["file_entries"].append(
        {
            "path": path,
            "change_type": "added",
            "before_hash": None,
            "after_hash": _sha(b"second promoted\n"),
            "content": "second promoted\n",
            "binary": False,
            "promotion_eligible": True,
            "before_content": None,
            "before_exists": False,
        }
    )
    ecp["file_count"] = 2
    ecp["promotion_eligible_count"] = 2
    per["file_plan"].append(path)
    per["file_results"].append({"path": path, "outcome": "success"})
    assert agent.store_execution_change_package(root, ecp)["stored"] is True
    assert agent.store_promotion_execution_record(root, per)["stored"] is True
    return target


def test_pre_3m_real_rollback_computes_and_consumes_evidence_without_dry_run(
    pre_3m_tree: Path, tmp_path: Path
) -> None:
    observed = _baseline(pre_3m_tree, tmp_path / "repo", "real")
    assert observed["result"]["status"] == "completed"
    assert observed["target_exists"] is False
    assert observed["record"]["file_plan"] == ["promoted.txt"]
    assert observed["record"]["divergence_check"]["blocking"] is False


def test_pre_3m_dry_run_is_optional_read_only_diagnostics(
    pre_3m_tree: Path, tmp_path: Path
) -> None:
    observed = _baseline(pre_3m_tree, tmp_path / "repo", "dry")
    assert observed["result"]["dry_run"] is True
    assert observed["result"]["file_plan"] == ["promoted.txt"]
    assert observed["result"]["divergence_check"]["blocking"] is False
    assert observed["record"] is None
    assert observed["target_exists"] is True


def test_pre_3m_divergence_is_consumed_before_permission_and_effect(
    pre_3m_tree: Path, tmp_path: Path
) -> None:
    observed = _baseline(pre_3m_tree, tmp_path / "repo", "divergence")
    assert observed["result"]["error"] == "divergence_conflict"
    assert observed["record"]["status"] == "aborted_divergence"
    assert observed["record"]["divergence_check"]["blocking"] is True
    assert observed["target_exists"] is True


def test_pre_3m_source_orders_preparation_before_dry_run_and_both_gates(pre_3m_tree: Path) -> None:
    source = (pre_3m_tree / "src/pcae/core/agent.py").read_text()
    body = source[source.index("def build_rollback_execution("):source.index("def mark_rollback_execution_interrupted(")]
    plan = body.index('file_plan = [r["path"]')
    divergence = body.index("divergence = _rer_check_divergence")
    dry = body.index("if dry_run:")
    hatp = body.index("HATP_MANDATORY")
    broker = body.index("evaluate_rollback_permission")
    effect = min(body.index("full_path.write_text"), body.index("full_path.unlink()"))
    assert plan < divergence < dry < hatp < broker < effect


def test_current_real_rollback_needs_no_prior_dry_run_and_surfaces_evidence(tmp_path: Path) -> None:
    root, target = _setup(tmp_path / "repo")
    result = agent.build_rollback_execution(root, "per-3m1")
    assert result["status"] == "completed"
    assert result["file_plan"] == ["promoted.txt"]
    assert result["divergence_check"]["blocking"] is False
    assert not target.exists()


def test_current_dry_run_is_read_only_and_persists_no_rer(tmp_path: Path) -> None:
    root, target = _setup(tmp_path / "repo")
    before = target.read_bytes()
    result = agent.build_rollback_execution(root, "per-3m1", dry_run=True)
    assert result["dry_run"] is True
    assert result["file_plan"] == ["promoted.txt"]
    assert target.read_bytes() == before
    assert not (root.path / ".pcae/rollback-executions").exists()


def test_divergence_surfaces_evidence_equal_to_persisted_and_bypasses_broker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, target = _setup(tmp_path / "repo")
    target.write_text("external change\n")
    calls = {"count": 0}

    def forbidden(*_args, **_kwargs):
        calls["count"] += 1
        raise AssertionError("broker must not run after divergence")

    monkeypatch.setattr(mutation_permission, "evaluate_rollback_permission", forbidden)
    result = agent.build_rollback_execution(root, "per-3m1")
    stored = agent.lookup_rollback_execution_record(root, result["rer_id"])
    assert result["error"] == "divergence_conflict"
    assert calls["count"] == 0
    assert result["file_plan"] == stored["file_plan"]
    assert result["divergence_check"] == stored["divergence_check"]
    assert target.read_text() == "external change\n"


def test_clean_evidence_plus_permission_broker_deny_is_non_authoritative(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, target = _setup(tmp_path / "repo")
    calls = _deny(monkeypatch)
    result = agent.build_rollback_execution(root, "per-3m1")
    stored = agent.lookup_rollback_execution_record(root, result["rer_id"])
    assert result["divergence_check"]["blocking"] is False
    assert result["error"] == "rollback_permission_denied"
    assert calls["count"] == 1
    assert target.exists()
    assert result["file_plan"] == stored["file_plan"]
    assert result["divergence_check"] == stored["divergence_check"]
    assert stored["rollback_executed"] is False


def test_hatp_denial_surfaces_same_evidence_and_never_calls_default_adapter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, target = _setup(tmp_path / "repo")
    monkeypatch.setattr(
        cutover,
        "resolve_production_hatp_cutover_mode",
        lambda _root: _fixed_mode(CutoverMode.HATP_MANDATORY),
    )
    calls = {"count": 0}

    def forbidden(*_args, **_kwargs):
        calls["count"] += 1
        raise AssertionError("default adapter is isolated from HATP mandatory")

    monkeypatch.setattr(mutation_permission, "evaluate_rollback_permission", forbidden)
    result = agent.build_rollback_execution(root, "per-3m1")
    stored = agent.lookup_rollback_execution_record(root, result["rer_id"])
    assert result["error"] == "hatp_evidence_required"
    assert result["file_plan"] == stored["file_plan"]
    assert result["divergence_check"] == stored["divergence_check"]
    assert calls["count"] == 0
    assert target.exists()


def test_completed_result_evidence_equals_persisted_record(tmp_path: Path) -> None:
    root, _target = _setup(tmp_path / "repo")
    result = agent.build_rollback_execution(root, "per-3m1")
    stored = agent.lookup_rollback_execution_record(root, result["rer_id"])
    assert result["file_plan"] == stored["file_plan"]
    assert result["divergence_check"] == stored["divergence_check"]
    assert stored["status"] == "completed"


def test_failed_final_result_surfaces_evidence_equal_to_persisted_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, target = _setup(tmp_path / "repo")
    real_unlink = Path.unlink

    def fail_target(path_obj: Path, *args, **kwargs):
        if path_obj == target:
            raise OSError("3m1 forced unlink failure")
        return real_unlink(path_obj, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_target)
    result = agent.build_rollback_execution(root, "per-3m1")
    stored = agent.lookup_rollback_execution_record(root, result["rer_id"])
    assert result["status"] == "failed"
    assert result["file_plan"] == stored["file_plan"]
    assert result["divergence_check"] == stored["divergence_check"]
    assert target.exists()


def test_partial_final_result_surfaces_evidence_equal_to_persisted_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, first = _setup(tmp_path / "repo")
    second = _add_second_path(root)
    real_unlink = Path.unlink

    def fail_second(path_obj: Path, *args, **kwargs):
        if path_obj == second:
            raise OSError("3m1 forced second unlink failure")
        return real_unlink(path_obj, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_second)
    result = agent.build_rollback_execution(root, "per-3m1")
    stored = agent.lookup_rollback_execution_record(root, result["rer_id"])
    assert result["status"] == "partial"
    assert result["file_plan"] == stored["file_plan"] == ["promoted.txt", "second.txt"]
    assert result["divergence_check"] == stored["divergence_check"]
    assert not first.exists()
    assert second.exists()


def test_current_state_is_recomputed_after_divergence_is_corrected(tmp_path: Path) -> None:
    root, target = _setup(tmp_path / "repo")
    target.write_text("external change\n")
    blocked = agent.build_rollback_execution(root, "per-3m1")
    assert blocked["divergence_check"]["file_checks"][0]["status"] == "conflict"
    target.write_text("promoted\n")
    retried = agent.build_rollback_execution(root, "per-3m1")
    assert retried["divergence_check"]["file_checks"][0]["status"] == "pending"
    assert retried["status"] == "completed"
    assert not target.exists()


def test_denied_retry_recomputes_then_can_proceed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, target = _setup(tmp_path / "repo")
    _deny(monkeypatch)
    denied = agent.build_rollback_execution(root, "per-3m1")
    assert denied["error"] == "rollback_permission_denied"
    assert target.exists()
    monkeypatch.undo()
    retried = agent.build_rollback_execution(root, "per-3m1")
    assert retried["status"] == "completed"
    assert retried["divergence_check"]["file_checks"][0]["status"] == "pending"
    assert not target.exists()


def test_reentry_uses_existing_already_reverted_idempotency_semantics(tmp_path: Path) -> None:
    root, target = _setup(tmp_path / "repo")
    first = agent.build_rollback_execution(root, "per-3m1")
    second = agent.build_rollback_execution(root, "per-3m1")
    assert first["status"] == second["status"] == "completed"
    assert first["reverted"] is True
    assert second["reverted"] is False
    assert second["divergence_check"]["file_checks"][0]["status"] == "already_reverted"
    assert second["file_results"][0]["outcome"] == "already_reverted"
    assert not target.exists()


def test_evidence_is_repository_local_and_not_cross_repo_reused(tmp_path: Path) -> None:
    root_a, _ = _setup(tmp_path / "a", current=b"promoted\n")
    root_b, target_b = _setup(tmp_path / "b", current=b"different promoted\n")
    target_b.write_text("external\n")
    a = agent.build_rollback_execution(root_a, "per-3m1", dry_run=True)
    b = agent.build_rollback_execution(root_b, "per-3m1", dry_run=True)
    assert a["divergence_check"]["blocking"] is False
    assert b["divergence_check"]["blocking"] is True
    assert a["divergence_check"] != b["divergence_check"]


def test_no_ag5_readiness_artifact_or_cache_is_created(tmp_path: Path) -> None:
    root, _ = _setup(tmp_path / "repo")
    before_paths = {p.relative_to(root.path) for p in root.path.rglob("*")}
    agent.build_rollback_execution(root, "per-3m1", dry_run=True)
    after_paths = {p.relative_to(root.path) for p in root.path.rglob("*")}
    assert after_paths == before_paths
    assert not any("readiness" in str(path).lower() for path in after_paths)


def test_literal_cli_dry_run_discloses_evidence_without_permission_claim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _setup(tmp_path / "repo")
    monkeypatch.chdir(tmp_path / "repo")
    rc = main(["rollback", "--per-id", "per-3m1", "--dry-run"])
    output = capsys.readouterr().out
    assert rc == 0
    assert "Rollback: DRY RUN" in output
    assert "file_plan:" in output
    assert "automatic_rollback_allowed=False" in output
    assert "AUTHORIZED" not in output


def test_literal_cli_real_call_without_prior_dry_run_surfaces_final_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _root, target = _setup(tmp_path / "repo")
    monkeypatch.chdir(tmp_path / "repo")
    rc = main(["rollback", "--per-id", "per-3m1"])
    output = capsys.readouterr().out
    assert rc == 0
    assert "Rollback: COMPLETED" in output
    assert "divergence_check:" in output
    assert "promoted.txt: success" in output
    assert "automatic_rollback_allowed=False" in output
    assert not target.exists()


def test_json_output_is_additive_and_truthful_on_denial(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _root, target = _setup(tmp_path / "repo")
    _deny(monkeypatch)
    monkeypatch.chdir(tmp_path / "repo")
    rc = main(["rollback", "--per-id", "per-3m1", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 1
    assert payload["error"] == "rollback_permission_denied"
    assert payload["file_plan"] == ["promoted.txt"]
    assert payload["divergence_check"]["blocking"] is False
    assert payload["execution_allowed"] is False
    assert target.exists()


def test_only_production_cli_calls_ag5_and_human_boundary_is_explicit() -> None:
    repo = Path(__file__).resolve().parents[1]
    hits = subprocess.run(
        ["rg", "-n", "build_rollback_execution\\(", "src/pcae"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.splitlines()
    callers = [line for line in hits if "def build_rollback_execution" not in line]
    assert callers
    assert all("src/pcae/commands/agent.py" in line for line in callers)
    assert agent._RER_GOVERNANCE_BOUNDARIES["automatic_rollback_allowed"] is False
    assert agent._RER_GOVERNANCE_BOUNDARIES["rollback_requires_explicit_human_command"] is True


def test_no_schema_or_record_contract_changed_in_3m() -> None:
    repo = Path(__file__).resolve().parents[1]
    changed = subprocess.run(
        ["git", "diff", "--name-only", PRE_3M_COMMIT, INTEGRATION_COMMIT, "--", "docs/contracts", "src/pcae/schema_resources"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    pre_version = subprocess.run(
        ["git", "show", f"{PRE_3M_COMMIT}:src/pcae/core/agent.py"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
    ).stdout
    assert changed == ""
    assert '_RER_VERSION: str = "1.0"' in pre_version
    assert agent._RER_VERSION == "1.0"


def test_3m_changed_result_visibility_not_gate_or_effect_statements(pre_3m_tree: Path) -> None:
    pre = (pre_3m_tree / "src/pcae/core/agent.py").read_text()
    post = Path(agent.__file__).read_text()
    for statement in (
        "if divergence[\"blocking\"]:",
        "mutation_permission.evaluate_rollback_permission(",
        "for path in file_plan:",
        "full_path.write_bytes(",
        "full_path.write_text(",
        "full_path.unlink()",
        'return 0 if result["status"] in ("completed", "partial") else 1',
    ):
        if statement.startswith("return 0"):
            pre_cli = (pre_3m_tree / "src/pcae/commands/agent.py").read_text()
            post_cli = Path(inspect.getfile(main)).parent / "commands" / "agent.py"
            assert pre_cli.count(statement) == post_cli.read_text().count(statement)
        else:
            assert pre.count(statement) == post.count(statement)


def test_a_b_effect_and_authority_match_with_visibility_as_only_result_delta(
    pre_3m_tree: Path, tmp_path: Path
) -> None:
    baseline = _baseline(pre_3m_tree, tmp_path / "pre", "real")
    current_root, current_target = _setup(tmp_path / "post")
    current = agent.build_rollback_execution(current_root, "per-3m1")
    assert baseline["result"]["status"] == current["status"] == "completed"
    assert baseline["result"]["reverted"] == current["reverted"] is True
    assert baseline["record"]["file_plan"] == current["file_plan"]
    assert baseline["record"]["divergence_check"] == current["divergence_check"]
    assert "file_plan" not in baseline["result"]
    assert "divergence_check" not in baseline["result"]
    assert not current_target.exists()


def test_runtime_remains_observe_only_after_rollback_evidence_operations(tmp_path: Path) -> None:
    before = subprocess.run(
        ["pcae", "runtime", "inspect"], text=True, capture_output=True, check=True
    ).stdout
    root, _ = _setup(tmp_path / "repo")
    agent.build_rollback_execution(root, "per-3m1", dry_run=True)
    after = subprocess.run(
        ["pcae", "runtime", "inspect"], text=True, capture_output=True, check=True
    ).stdout
    for output in (before, after):
        assert "Runtime state:             Observed" in output
        assert "Maximum plugin capability: observe" in output
        assert "Execution capability:      unavailable" in output
    assert before == after


def test_result_field_consumers_have_no_strict_rollback_key_set_assumption() -> None:
    repo = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            "rg",
            "-n",
            r"result\.keys\(\)[^\n]*==|==[^\n]*result\.keys\(\)",
            "src/pcae",
            "tests",
        ],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    relevant = [line for line in result.stdout.splitlines() if "rollback" in line.lower()]
    assert relevant == []
