"""Lifecycle regression tests for the 77J-77V.1 backend-created output adoption lifecycle.

These tests protect the major invariants proven by the completed lifecycle:
mutation detection, adoption gates, commit/push safety, hook-bypass reconciliation,
final verification, and metadata consistency.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

pytestmark = [pytest.mark.slow, pytest.mark.integration, pytest.mark.phase_closure]

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.paths import HarnessPath


def _init(tmp_path: Path, monkeypatch) -> Path:
    init_harness(HarnessPath(tmp_path))
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True, capture_output=True, text=True)


def _write_artifact(root: Path, rel_dir: str, data: dict) -> None:
    d = root / ".pcae" / rel_dir
    d.mkdir(parents=True, exist_ok=True)
    (d / ".gitignore").write_text("*\n")
    (d / "latest.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_file(root: Path, rel_path: str, content: str) -> None:
    p = root / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def _commit_baseline(root: Path) -> None:
    subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=root, check=True, capture_output=True)


# ── A. Adoption execution blocks without approval/preflight ──


def test_adoption_execution_blocks_without_approval(tmp_path, monkeypatch, capsys):
    """Adoption execution must block when approval artifact is missing."""
    _init(tmp_path, monkeypatch)
    main(["phase", "backend-created-output-adoption-execution", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["backend_created_output_adoption_execution_status"] != "staged_for_future_commit"
    assert d["push_performed"] is False
    assert d["backend_invocation_performed"] is False
    assert len(d["blockers"]) > 0


def test_adoption_execution_does_not_push(tmp_path, monkeypatch, capsys):
    """Adoption execution must never push, even in execute mode."""
    _init(tmp_path, monkeypatch)
    main(["phase", "backend-created-output-adoption-execution", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["push_performed"] is False
    assert d.get("pcae_push_performed", False) is False
    assert d.get("raw_git_push_performed", False) is False
    assert d.get("force_push_performed", False) is False


# ── B. Commit approval blocks with missing/wrong prerequisites ──


def test_commit_approval_blocks_without_execution(tmp_path, monkeypatch, capsys):
    """Commit approval must block when adoption execution artifact is missing."""
    _init(tmp_path, monkeypatch)
    main(["phase", "backend-created-output-adoption-commit-approval", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["backend_created_output_adoption_commit_approval_status"] != "approved"
    assert d["backend_created_output_adoption_commit_approval_status"] != "ready_for_commit_approval"
    assert len(d["blockers"]) > 0
    assert d["push_performed"] is False


def test_commit_execution_blocks_without_approval(tmp_path, monkeypatch, capsys):
    """Commit execution must block when commit approval is missing."""
    _init(tmp_path, monkeypatch)
    main(["phase", "backend-created-output-adoption-commit-execution", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["backend_created_output_adoption_commit_execution_status"] != "committed_for_future_push"
    assert d["push_performed"] is False
    assert d["backend_invocation_performed"] is False


def test_commit_execution_does_not_push(tmp_path, monkeypatch, capsys):
    """Commit execution must never push."""
    _init(tmp_path, monkeypatch)
    main(["phase", "backend-created-output-adoption-commit-execution", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["push_performed"] is False
    assert d.get("pcae_push_performed", False) is False
    assert d.get("force_push_performed", False) is False


# ── C. Hook-bypass reconciliation regressions ──


def test_final_verification_blocks_unreachable_adoption_commit(tmp_path, monkeypatch, capsys):
    """Final verification must block when adoption commit is not reachable from origin/main."""
    root = _init(tmp_path, monkeypatch)
    _write_artifact(root, "backend-created-output-adoption-push-executions", {
        "backend_created_output_adoption_push_execution_status": "pushed",
        "push_performed": True,
        "adoption_commit_hash": "abc123nonexistent",
    })
    _write_artifact(root, "adoption-commit-hook-bypass-reconciliations", {
        "hook_bypass_reconciliation_status": "reconciled_documented_exception",
        "hook_bypass_normalized": False,
        "hook_bypass_policy_recorded": True,
    })
    _commit_baseline(root)
    main(["phase", "backend-created-output-adoption-final-verification", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["backend_created_output_adoption_final_verification_status"] == "adoption_commit_not_reachable"
    assert len(d["blockers"]) > 0


def test_tooling_push_blocks_missing_reconciliation(tmp_path, monkeypatch, capsys):
    """Missing reconciliation must block tooling push decision."""
    root = _init(tmp_path, monkeypatch)
    _write_artifact(root, "backend-created-output-adoption-final-verifications", {
        "backend_created_output_adoption_final_verification_status": "verified",
        "lifecycle_closed": True,
    })
    _commit_baseline(root)
    main(["phase", "final-verification-tooling-push-decision", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["final_verification_tooling_push_decision_status"] == "hook_bypass_reconciliation_missing"
    assert d["push_performed"] is False


# ── D. Push safety regressions ──


def test_push_approval_blocks_without_prerequisites(tmp_path, monkeypatch, capsys):
    """Push approval must block when commit execution artifact is missing."""
    _init(tmp_path, monkeypatch)
    main(["phase", "backend-created-output-adoption-push-approval", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["backend_created_output_adoption_push_approval_status"] != "approved"
    assert d["push_performed"] is False
    assert len(d["blockers"]) > 0


def test_push_execution_blocks_without_approval(tmp_path, monkeypatch, capsys):
    """Push execution must block when push approval is missing."""
    _init(tmp_path, monkeypatch)
    main(["phase", "backend-created-output-adoption-push-execution", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["backend_created_output_adoption_push_execution_status"] == "missing_push_approval"
    assert d["push_performed"] is False
    assert d.get("force_push_performed", False) is False


def test_push_execution_default_does_not_push(tmp_path, monkeypatch, capsys):
    """Push execution in default/dry-run mode must not actually push."""
    root = _init(tmp_path, monkeypatch)
    _write_artifact(root, "backend-created-output-adoption-push-approvals", {
        "backend_created_output_adoption_push_approval_status": "approved",
        "human_push_approval_granted": True,
        "approved_commit_hashes": [],
        "approved_unpushed_commit_count": 0,
    })
    main(["phase", "backend-created-output-adoption-push-execution", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["push_performed"] is False


def test_push_execution_blocks_dirty_tree(tmp_path, monkeypatch, capsys):
    """Push execution must block when working tree is dirty."""
    root = _init(tmp_path, monkeypatch)
    _write_artifact(root, "backend-created-output-adoption-push-approvals", {
        "backend_created_output_adoption_push_approval_status": "approved",
        "human_push_approval_granted": True,
        "approved_commit_hashes": ["abc123"],
        "approved_unpushed_commit_count": 1,
    })
    subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=root, check=True, capture_output=True)
    _write_file(root, "dirty.txt", "dirty")
    main(["phase", "backend-created-output-adoption-push-execution", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["backend_created_output_adoption_push_execution_status"] == "dirty_working_tree"
    assert d["push_performed"] is False


# ── E. Final verification regressions ──


def test_final_verification_blocks_without_push_execution(tmp_path, monkeypatch, capsys):
    """Final verification must block when push execution artifact is missing."""
    _init(tmp_path, monkeypatch)
    main(["phase", "backend-created-output-adoption-final-verification", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["backend_created_output_adoption_final_verification_status"] == "missing_push_execution"
    assert d["push_performed"] is False
    assert d["backend_invocation_performed"] is False
    assert d["docs_file_modified_in_this_phase"] is False


def test_final_verification_does_not_push(tmp_path, monkeypatch, capsys):
    """Final verification must never push or invoke backend."""
    _init(tmp_path, monkeypatch)
    main(["phase", "backend-created-output-adoption-final-verification", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["push_performed"] is False
    assert d["backend_invocation_performed"] is False
    assert d.get("pcae_push_performed", False) is False
    assert d.get("force_push_performed", False) is False
    assert d.get("raw_git_push_performed", False) is False


# ── F. Tooling push decision regressions ──


def test_tooling_push_blocks_unexpected_commits(tmp_path, monkeypatch, capsys):
    """Tooling push decision must block non-77V/77V.1 commits."""
    root = _init(tmp_path, monkeypatch)
    _write_artifact(root, "backend-created-output-adoption-final-verifications", {
        "backend_created_output_adoption_final_verification_status": "verified",
        "lifecycle_closed": True,
        "final_verification_outcome": "adoption_lifecycle_complete",
    })
    _write_artifact(root, "adoption-commit-hook-bypass-reconciliations", {
        "hook_bypass_reconciliation_status": "reconciled_documented_exception",
        "hook_bypass_normalized": False,
        "hook_bypass_policy_recorded": True,
    })
    subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "checkout", "-b", "test-remote"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "checkout", "main" if _has_main(root) else "master"], cwd=root, check=True, capture_output=True)
    _write_file(root, "unexpected.txt", "unexpected")
    subprocess.run(["git", "add", "unexpected.txt"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Unexpected unrelated commit"], cwd=root, check=True, capture_output=True)
    main(["phase", "final-verification-tooling-push-decision", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["final_verification_tooling_push_decision_status"] in (
        "unexpected_unpushed_commits", "missing_77v_tooling_commit",
        "adoption_lifecycle_not_verified", "dirty_working_tree",
    )
    assert d["push_performed"] is False
    assert d["force_push_performed"] is False


def test_tooling_push_blocks_without_verification(tmp_path, monkeypatch, capsys):
    """Tooling push decision must block when 77V verification is missing."""
    _init(tmp_path, monkeypatch)
    main(["phase", "final-verification-tooling-push-decision", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["final_verification_tooling_push_decision_status"] == "adoption_lifecycle_not_verified"
    assert d["push_performed"] is False


def test_tooling_push_blocks_hook_bypass_normalized(tmp_path, monkeypatch, capsys):
    """Tooling push decision must block when hook bypass was normalized."""
    root = _init(tmp_path, monkeypatch)
    _write_artifact(root, "backend-created-output-adoption-final-verifications", {
        "backend_created_output_adoption_final_verification_status": "verified",
        "lifecycle_closed": True,
    })
    _write_artifact(root, "adoption-commit-hook-bypass-reconciliations", {
        "hook_bypass_reconciliation_status": "reconciled_documented_exception",
        "hook_bypass_normalized": True,
        "hook_bypass_policy_recorded": True,
    })
    _commit_baseline(root)
    main(["phase", "final-verification-tooling-push-decision", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["final_verification_tooling_push_decision_status"] == "hook_bypass_normalized"
    assert d["push_performed"] is False


# ── G. No lifecycle command invokes backend or runner ──


@pytest.mark.parametrize("cmd", [
    "backend-created-output-adoption-execution",
    "backend-created-output-adoption-commit-approval",
    "backend-created-output-adoption-commit-execution",
    "backend-created-output-adoption-push-approval",
    "backend-created-output-adoption-push-execution",
    "backend-created-output-adoption-final-verification",
    "final-verification-tooling-push-decision",
])
def test_lifecycle_commands_never_invoke_backend(tmp_path, monkeypatch, capsys, cmd):
    """No lifecycle command should invoke a backend or perform runner execution."""
    _init(tmp_path, monkeypatch)
    main(["phase", cmd, "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d.get("backend_invocation_performed", False) is False
    assert d.get("runner_execute_performed", False) is False
    assert d.get("force_push_performed", False) is False


def _has_main(root: Path) -> bool:
    r = subprocess.run(
        ["git", "branch", "--list", "main"],
        cwd=root, capture_output=True, text=True,
    )
    return "main" in r.stdout
