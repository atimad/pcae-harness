"""Tests for lifecycle gate runner dry-run (Phase 80D)."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.paths import HarnessPath
from pcae.lifecycle import evaluate_gate_dry_run, GATE_DEFINITIONS


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


# ── Core dry-run behavior ──


def test_known_gate_returns_read_only():
    r = evaluate_gate_dry_run("final_verification", "pushed")
    assert r["read_only"] is True
    assert r["dry_run"] is True
    assert r["lifecycle_gate_dry_run_status"] == "ready"


def test_known_gate_no_execution_flags():
    r = evaluate_gate_dry_run("adoption_execution", "adoption_execution_ready")
    assert r["gate_execution_performed"] is False
    assert r["approval_performed"] is False
    assert r["backend_invocation_performed"] is False
    assert r["commit_performed"] is False
    assert r["push_performed"] is False
    assert r["force_push_performed"] is False
    assert r["raw_git_push_performed"] is False
    assert r["runner_execute_performed"] is False
    assert r["execution_authorized"] is False


def test_unknown_gate_blocks():
    r = evaluate_gate_dry_run("nonexistent_gate", "idle")
    assert r["lifecycle_gate_dry_run_status"] == "unknown_gate"
    assert len(r["blockers"]) > 0


def test_without_dry_run_blocks(tmp_path, monkeypatch, capsys):
    _init(tmp_path, monkeypatch)
    exit_code = main(["lifecycle", "backend-output-adoption", "run-gate",
                       "--gate", "final_verification", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["lifecycle_gate_dry_run_status"] == "dry_run_required"
    assert exit_code == 1


def test_illegal_transition_blocks():
    r = evaluate_gate_dry_run("push_execution", "idle")
    assert r["lifecycle_gate_dry_run_status"] == "illegal_transition"
    assert len(r["blockers"]) > 0


# ── Gate-specific behavior ──


def test_approval_gate_reports_required_approval():
    r = evaluate_gate_dry_run("adoption_approval", "adoption_reviewed")
    assert r["lifecycle_gate_dry_run_status"] == "ready"
    assert "operator adoption approval" in r["required_approvals"]
    assert r["approval_performed"] is False


def test_execution_gate_reports_dangerous_but_no_execute():
    r = evaluate_gate_dry_run("commit_execution", "commit_approved")
    assert r["lifecycle_gate_dry_run_status"] == "ready"
    assert "DANGEROUS" in r["planned_action_summary"]
    assert r["gate_execution_performed"] is False
    assert r["commit_performed"] is False


def test_push_execution_no_push():
    r = evaluate_gate_dry_run("push_execution", "push_approved")
    assert r["push_performed"] is False
    assert r["force_push_performed"] is False
    assert r["raw_git_push_performed"] is False


def test_backend_capture_no_backend():
    r = evaluate_gate_dry_run("backend_capture", "backend_capture_attempted")
    assert r["backend_invocation_performed"] is False


# ── State-dependent behavior ──


def test_closed_lifecycle_blocks_dangerous_gates():
    r = evaluate_gate_dry_run("adoption_execution", "closed")
    assert r["lifecycle_gate_dry_run_status"] == "illegal_transition"
    assert "closed" in r["blockers"][0].lower()


def test_staged_allows_commit_approval_dry_run():
    r = evaluate_gate_dry_run("commit_approval", "staged_for_commit")
    assert r["lifecycle_gate_dry_run_status"] == "ready"


def test_staged_blocks_commit_execution():
    r = evaluate_gate_dry_run("commit_execution", "staged_for_commit")
    assert r["lifecycle_gate_dry_run_status"] == "illegal_transition"


def test_committed_allows_push_approval_dry_run():
    r = evaluate_gate_dry_run("push_approval", "committed_for_push")
    assert r["lifecycle_gate_dry_run_status"] == "ready"


def test_committed_blocks_push_execution():
    r = evaluate_gate_dry_run("push_execution", "committed_for_push")
    assert r["lifecycle_gate_dry_run_status"] == "illegal_transition"


# ── CLI integration ──


def test_cli_dry_run_json(tmp_path, monkeypatch, capsys):
    _init(tmp_path, monkeypatch)
    main(["lifecycle", "backend-output-adoption", "run-gate",
           "--gate", "final_verification", "--dry-run", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["dry_run"] is True
    assert d["read_only"] is True
    assert d["gate"] == "final_verification"


def test_cli_does_not_create_files(tmp_path, monkeypatch, capsys):
    root = _init(tmp_path, monkeypatch)
    files_before = set(root.rglob("*"))
    main(["lifecycle", "backend-output-adoption", "run-gate",
           "--gate", "adoption_review", "--dry-run", "--json"])
    capsys.readouterr()
    files_after = set(root.rglob("*"))
    assert files_before == files_after


def test_json_contains_required_fields(tmp_path, monkeypatch, capsys):
    _init(tmp_path, monkeypatch)
    main(["lifecycle", "backend-output-adoption", "run-gate",
           "--gate", "backend_capture_preflight", "--dry-run", "--json"])
    d = json.loads(capsys.readouterr().out)
    required = {
        "lifecycle_gate_dry_run_status", "lifecycle_type", "gate",
        "current_state", "target_state", "gate_kind", "dry_run",
        "read_only", "gate_execution_performed", "approval_performed",
        "backend_invocation_performed", "commit_performed", "push_performed",
        "raw_git_push_performed", "force_push_performed", "runner_execute_performed",
        "execution_authorized", "required_artifacts", "required_approvals",
        "required_preconditions", "blockers", "warnings", "planned_action_summary",
    }
    assert required <= set(d.keys())
