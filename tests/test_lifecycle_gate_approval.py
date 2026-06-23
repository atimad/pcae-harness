"""Tests for lifecycle gate approval command (Phase 80E).

Tests that approval records human sign-off for a gate without executing it.
Approval is separate from execution; execution_authorized is always false.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.paths import HarnessPath
from pcae.lifecycle import evaluate_gate_approval


def _init(tmp_path: Path, monkeypatch) -> Path:
    init_harness(HarnessPath(tmp_path))
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True, capture_output=True)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _write_artifact(root: Path, rel_dir: str, data: dict) -> None:
    d = root / ".pcae" / rel_dir
    d.mkdir(parents=True, exist_ok=True)
    (d / ".gitignore").write_text("*\n")
    (d / "latest.json").write_text(json.dumps(data) + "\n", encoding="utf-8")


# ── Input validation ──


def test_unknown_gate_blocks():
    r = evaluate_gate_approval("nonexistent", "idle", "Op", "test")
    assert r["lifecycle_gate_approval_status"] == "unknown_gate"
    assert len(r["blockers"]) > 0
    assert r["execution_authorized"] is False


def test_missing_approver_blocks():
    r = evaluate_gate_approval("adoption_approval", "adoption_reviewed", "", "reason")
    assert r["lifecycle_gate_approval_status"] == "missing_approver"
    assert r["execution_authorized"] is False


def test_missing_reason_blocks():
    r = evaluate_gate_approval("adoption_approval", "adoption_reviewed", "Op", "")
    assert r["lifecycle_gate_approval_status"] == "missing_reason"
    assert r["execution_authorized"] is False


# ── Approval behavior ──


def test_approval_gate_can_be_approved():
    r = evaluate_gate_approval("adoption_approval", "adoption_reviewed", "Operator", "Approved for adoption")
    assert r["lifecycle_gate_approval_status"] == "approved"
    assert r["approval_performed"] is True
    assert r["execution_authorized"] is False
    assert r["gate_execution_performed"] is False


def test_approval_records_execution_authorized_false():
    r = evaluate_gate_approval("adoption_approval", "adoption_reviewed", "Op", "test")
    assert r["execution_authorized"] is False


def test_approval_all_execution_flags_false():
    r = evaluate_gate_approval("commit_approval", "staged_for_commit", "Op", "test")
    assert r["gate_execution_performed"] is False
    assert r["backend_invocation_performed"] is False
    assert r["adoption_execution_performed"] is False
    assert r["commit_performed"] is False
    assert r["push_performed"] is False
    assert r["raw_git_push_performed"] is False
    assert r["force_push_performed"] is False
    assert r["runner_execute_performed"] is False
    assert r["execution_authorized"] is False


def test_approval_does_not_execute_gate():
    r = evaluate_gate_approval("push_approval", "hook_bypass_reconciled", "Op", "push ok")
    assert r["lifecycle_gate_approval_status"] == "approved"
    assert r["gate_execution_performed"] is False
    assert r["push_performed"] is False


# ── Dry-run behavior ──


def test_dry_run_does_not_record_approval():
    r = evaluate_gate_approval("adoption_approval", "adoption_reviewed", "Op", "test", dry_run=True)
    assert r["lifecycle_gate_approval_status"] == "dry_run"
    assert r["approval_performed"] is False
    assert r["dry_run"] is True


def test_dry_run_does_not_write_files(tmp_path, monkeypatch, capsys):
    root = _init(tmp_path, monkeypatch)
    files_before = set(root.rglob("*"))
    main(["lifecycle", "backend-output-adoption", "approve-gate",
           "--gate", "adoption_approval", "--approved-by", "Op",
           "--reason", "test", "--dry-run", "--json"])
    capsys.readouterr()
    files_after = set(root.rglob("*"))
    assert files_before == files_after


# ── Non-approval gate behavior ──


def test_non_approval_gate_reports_not_required():
    r = evaluate_gate_approval("quarantine_review", "mutation_detected", "Op", "review")
    assert r["lifecycle_gate_approval_status"] == "approval_not_required"
    assert "does not require approval" in r["warnings"][0]


# ── State validation ──


def test_illegal_state_blocks_approval():
    r = evaluate_gate_approval("adoption_approval", "idle", "Op", "test")
    assert r["lifecycle_gate_approval_status"] == "illegal_state_for_approval"
    assert len(r["blockers"]) > 0


def test_closed_blocks_adoption_approval():
    r = evaluate_gate_approval("adoption_approval", "closed", "Op", "test")
    assert r["lifecycle_gate_approval_status"] == "illegal_state_for_approval"


# ── CLI integration ──


def test_cli_approve_gate_json(tmp_path, monkeypatch, capsys):
    root = _init(tmp_path, monkeypatch)
    # Set up adoption_reviewed state so adoption_approval is legal
    _write_artifact(root, "backend-created-output-adoption-reviews", {
        "backend_created_output_adoption_review_status": "reviewed_adoption_candidate",
    })
    main(["lifecycle", "backend-output-adoption", "approve-gate",
           "--gate", "adoption_approval", "--approved-by", "Operator",
           "--reason", "test approval", "--dry-run", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["lifecycle_gate_approval_status"] == "dry_run"
    assert d["execution_authorized"] is False
    assert d["dry_run"] is True


def test_existing_dry_run_runner_still_requires_flag(tmp_path, monkeypatch, capsys):
    """80D run-gate without --dry-run must still block."""
    _init(tmp_path, monkeypatch)
    exit_code = main(["lifecycle", "backend-output-adoption", "run-gate",
                       "--gate", "final_verification", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["lifecycle_gate_dry_run_status"] == "dry_run_required"
    assert exit_code == 1


def test_approval_json_serializable():
    r = evaluate_gate_approval("adoption_approval", "adoption_reviewed", "Op", "test")
    s = json.dumps(r)
    assert isinstance(s, str)
    parsed = json.loads(s)
    assert parsed["lifecycle_gate_approval_status"] == "approved"
