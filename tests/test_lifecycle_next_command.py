"""Tests for lifecycle next-step recommendation command (Phase 80C)."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.paths import HarnessPath


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


def test_closed_recommends_new_lifecycle(tmp_path, monkeypatch, capsys):
    root = _init(tmp_path, monkeypatch)
    _write_artifact(root, "final-verification-tooling-push-decisions", {
        "final_verification_tooling_push_decision_status": "pushed_77v_tooling",
    })
    main(["lifecycle", "backend-output-adoption", "next", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["recommended_next_action"] == "start_new_lifecycle"
    assert d["read_only"] is True
    assert d["execution_performed"] is False


def test_mutation_detected_recommends_quarantine(tmp_path, monkeypatch, capsys):
    root = _init(tmp_path, monkeypatch)
    _write_artifact(root, "backend-retry-mutation-result-intakes", {
        "outcome": "repo_mutation_detected_with_output",
    })
    main(["lifecycle", "backend-output-adoption", "next", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["recommended_next_action"] == "quarantine_review"


def test_reviewed_recommends_approval(tmp_path, monkeypatch, capsys):
    root = _init(tmp_path, monkeypatch)
    _write_artifact(root, "backend-created-output-adoption-reviews", {
        "backend_created_output_adoption_review_status": "reviewed_adoption_candidate",
    })
    main(["lifecycle", "backend-output-adoption", "next", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["recommended_next_action"] == "adoption_approval"
    assert d["required_approval"] is True


def test_approved_recommends_preflight(tmp_path, monkeypatch, capsys):
    root = _init(tmp_path, monkeypatch)
    _write_artifact(root, "backend-created-output-adoption-approvals", {
        "backend_created_output_adoption_approval_status": "approved",
    })
    main(["lifecycle", "backend-output-adoption", "next", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["recommended_next_action"] == "execution_preflight"


def test_staged_recommends_commit_approval(tmp_path, monkeypatch, capsys):
    root = _init(tmp_path, monkeypatch)
    _write_artifact(root, "backend-created-output-adoption-executions", {
        "backend_created_output_adoption_execution_status": "staged_for_future_commit",
    })
    main(["lifecycle", "backend-output-adoption", "next", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["recommended_next_action"] == "commit_approval"


def test_committed_recommends_push_path(tmp_path, monkeypatch, capsys):
    root = _init(tmp_path, monkeypatch)
    _write_artifact(root, "backend-created-output-adoption-commit-executions", {
        "backend_created_output_adoption_commit_execution_status": "committed_for_future_push",
    })
    main(["lifecycle", "backend-output-adoption", "next", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["recommended_next_action"] in ("hook_bypass_reconciliation", "push_approval")


def test_pushed_recommends_final_verification(tmp_path, monkeypatch, capsys):
    root = _init(tmp_path, monkeypatch)
    _write_artifact(root, "backend-created-output-adoption-push-executions", {
        "backend_created_output_adoption_push_execution_status": "pushed",
    })
    main(["lifecycle", "backend-output-adoption", "next", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["recommended_next_action"] == "final_verification"


def test_idle_recommends_start(tmp_path, monkeypatch, capsys):
    _init(tmp_path, monkeypatch)
    main(["lifecycle", "backend-output-adoption", "next", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["recommended_next_action"] == "start_backend_capture"
    assert d["read_only"] is True


def test_next_json_has_all_safety_flags(tmp_path, monkeypatch, capsys):
    _init(tmp_path, monkeypatch)
    main(["lifecycle", "backend-output-adoption", "next", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["read_only"] is True
    assert d["execution_performed"] is False
    assert d["approval_performed"] is False
    assert d["backend_invocation_performed"] is False
    assert d["runner_execute_performed"] is False
    assert d["push_performed"] is False
    assert d["force_push_performed"] is False
    assert d["raw_git_push_performed"] is False
