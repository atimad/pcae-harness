"""Tests for lifecycle status command (Phase 80B)."""
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


def test_idle_status(tmp_path, monkeypatch, capsys):
    _init(tmp_path, monkeypatch)
    main(["lifecycle", "backend-output-adoption", "status", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["current_state"] == "idle"
    assert d["read_only"] is True
    assert d["execution_allowed_now"] is False
    assert d["backend_invocation_performed"] is False
    assert d["push_performed"] is False


def test_closed_status(tmp_path, monkeypatch, capsys):
    root = _init(tmp_path, monkeypatch)
    _write_artifact(root, "final-verification-tooling-push-decisions", {
        "final_verification_tooling_push_decision_status": "pushed_77v_tooling",
    })
    main(["lifecycle", "backend-output-adoption", "status", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["current_state"] == "closed"
    assert d["lifecycle_closed"] is True
    assert d["read_only"] is True


def test_blocked_missing_artifacts(tmp_path, monkeypatch, capsys):
    """Missing artifacts should report idle, not crash."""
    root = _init(tmp_path, monkeypatch)
    main(["lifecycle", "backend-output-adoption", "status", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["current_state"] in ("idle", "blocked", "unknown")
    assert d["read_only"] is True


def test_mutation_detected_status(tmp_path, monkeypatch, capsys):
    root = _init(tmp_path, monkeypatch)
    _write_artifact(root, "backend-retry-mutation-result-intakes", {
        "outcome": "repo_mutation_detected_with_output",
    })
    main(["lifecycle", "backend-output-adoption", "status", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["current_state"] == "mutation_detected"


def test_status_json_has_no_execution_flags(tmp_path, monkeypatch, capsys):
    _init(tmp_path, monkeypatch)
    main(["lifecycle", "backend-output-adoption", "status", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["execution_allowed_now"] is False
    assert d["backend_invocation_performed"] is False
    assert d["runner_execute_performed"] is False
    assert d["push_performed"] is False
    assert d["force_push_performed"] is False
    assert d["raw_git_push_performed"] is False


def test_status_does_not_create_files(tmp_path, monkeypatch, capsys):
    root = _init(tmp_path, monkeypatch)
    files_before = set(root.rglob("*"))
    main(["lifecycle", "backend-output-adoption", "status", "--json"])
    capsys.readouterr()
    files_after = set(root.rglob("*"))
    assert files_before == files_after
