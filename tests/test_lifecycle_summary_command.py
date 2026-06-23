"""Tests for lifecycle final summary command (Phase 80F).

Tests that the summary command aggregates lifecycle state, gates, approvals,
blockers, safety flags, and command capabilities in a read-only report.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.paths import HarnessPath
from pcae.lifecycle import build_lifecycle_summary


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


# ── Core summary behavior ──


def test_summary_exists_and_supports_json(tmp_path, monkeypatch, capsys):
    _init(tmp_path, monkeypatch)
    main(["lifecycle", "backend-output-adoption", "summary", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["lifecycle_summary_status"] == "summarized"
    assert d["lifecycle_type"] == "backend-output-adoption"


def test_summary_reports_current_state(tmp_path, monkeypatch, capsys):
    _init(tmp_path, monkeypatch)
    main(["lifecycle", "backend-output-adoption", "summary", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert "current_state" in d
    assert "current_state_label" in d


def test_summary_reports_gate_count_and_categories(tmp_path, monkeypatch, capsys):
    _init(tmp_path, monkeypatch)
    main(["lifecycle", "backend-output-adoption", "summary", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["gate_count"] > 0
    assert d["approval_gate_count"] > 0
    assert d["execution_gate_count"] > 0
    assert isinstance(d["gates"], list)
    for g in d["gates"]:
        assert "gate_id" in g
        assert "kind" in g
        assert "approval_required" in g


def test_summary_reports_command_capabilities(tmp_path, monkeypatch, capsys):
    _init(tmp_path, monkeypatch)
    main(["lifecycle", "backend-output-adoption", "summary", "--json"])
    d = json.loads(capsys.readouterr().out)
    caps = d["command_capabilities"]
    assert caps["status_command"] is True
    assert caps["next_command"] is True
    assert caps["gate_dry_run_command"] is True
    assert caps["gate_approval_command"] is True
    assert caps["non_dry_run_runner_command"] is False
    assert caps["final_summary_command"] is True


def test_summary_reports_next_action(tmp_path, monkeypatch, capsys):
    _init(tmp_path, monkeypatch)
    main(["lifecycle", "backend-output-adoption", "summary", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert "next_recommended_action" in d


def test_summary_safety_flags_all_false(tmp_path, monkeypatch, capsys):
    _init(tmp_path, monkeypatch)
    main(["lifecycle", "backend-output-adoption", "summary", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["execution_authorized"] is False
    assert d["gate_execution_performed"] is False
    assert d["approval_performed"] is False
    assert d["backend_invocation_performed"] is False
    assert d["adoption_execution_performed"] is False
    assert d["commit_performed"] is False
    assert d["push_performed"] is False
    assert d["raw_git_push_performed"] is False
    assert d["force_push_performed"] is False
    assert d["runner_execute_performed"] is False
    assert d["read_only"] is True
    assert d["summary_generated"] is True


def test_summary_confirms_non_dry_run_runner_absent(tmp_path, monkeypatch, capsys):
    _init(tmp_path, monkeypatch)
    main(["lifecycle", "backend-output-adoption", "summary", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["command_capabilities"]["non_dry_run_runner_command"] is False
    assert d["safety_summary"]["non_dry_run_runner_absent"] is True


def test_summary_does_not_approve_gates(tmp_path, monkeypatch, capsys):
    _init(tmp_path, monkeypatch)
    main(["lifecycle", "backend-output-adoption", "summary", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["approval_performed"] is False


def test_summary_does_not_execute_gates(tmp_path, monkeypatch, capsys):
    _init(tmp_path, monkeypatch)
    main(["lifecycle", "backend-output-adoption", "summary", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["gate_execution_performed"] is False


def test_summary_does_not_write_approval_artifacts(tmp_path, monkeypatch, capsys):
    root = _init(tmp_path, monkeypatch)
    files_before = set(root.rglob("*"))
    main(["lifecycle", "backend-output-adoption", "summary", "--json"])
    capsys.readouterr()
    files_after = set(root.rglob("*"))
    assert files_before == files_after


def test_summary_does_not_modify_files(tmp_path, monkeypatch, capsys):
    root = _init(tmp_path, monkeypatch)
    files_before = set(root.rglob("*"))
    main(["lifecycle", "backend-output-adoption", "summary", "--json"])
    capsys.readouterr()
    files_after = set(root.rglob("*"))
    assert files_before == files_after


def test_summary_handles_blocked_status(tmp_path, monkeypatch):
    r = build_lifecycle_summary(tmp_path)
    assert r["lifecycle_summary_status"] in ("summarized", "blocked", "unknown")
    assert r["read_only"] is True


def test_summary_handles_closed_lifecycle(tmp_path, monkeypatch, capsys):
    root = _init(tmp_path, monkeypatch)
    _write_artifact(root, "final-verification-tooling-push-decisions", {
        "final_verification_tooling_push_decision_status": "pushed_77v_tooling",
    })
    main(["lifecycle", "backend-output-adoption", "summary", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["current_state"] == "closed"
    assert d["lifecycle_closed"] is True


# ── Cross-command regression ──


def test_run_gate_without_dry_run_still_blocks(tmp_path, monkeypatch, capsys):
    _init(tmp_path, monkeypatch)
    exit_code = main(["lifecycle", "backend-output-adoption", "run-gate",
                       "--gate", "final_verification", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["lifecycle_gate_dry_run_status"] == "dry_run_required"
    assert exit_code == 1


def test_approve_gate_dry_run_does_not_write(tmp_path, monkeypatch, capsys):
    root = _init(tmp_path, monkeypatch)
    _write_artifact(root, "backend-created-output-adoption-reviews", {
        "backend_created_output_adoption_review_status": "reviewed_adoption_candidate",
    })
    files_before = set(root.rglob("*"))
    main(["lifecycle", "backend-output-adoption", "approve-gate",
           "--gate", "adoption_approval", "--approved-by", "Op",
           "--reason", "test", "--dry-run", "--json"])
    d = json.loads(capsys.readouterr().out)
    files_after = set(root.rglob("*"))
    assert files_before == files_after
    assert d["execution_authorized"] is False
