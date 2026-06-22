"""Tests for staged-file-aware task finish (Phase 79B).

Tests that pcae task finish --commit --staged-file-aware commits only
task-finish paths while preserving unrelated pre-existing staged files.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.paths import HarnessPath
from pcae.core.tasks import create_task_contract


def _init(tmp_path: Path, monkeypatch) -> Path:
    init_harness(HarnessPath(tmp_path))
    _init_git(tmp_path)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _init_git(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=root, check=True, capture_output=True)


def _write(root: Path, rel: str, content: str = "content\n") -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True)


def _staged(root: Path) -> list[str]:
    r = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=root, capture_output=True, text=True)
    return [l for l in r.stdout.strip().split("\n") if l]


def _blob_hash(root: Path, path: str) -> str:
    r = subprocess.run(["git", "rev-parse", f":0:{path}"], cwd=root, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def _create_active_task(root: Path) -> str:
    """Create a minimal active task and commit it so pcae sees it."""
    hr = HarnessPath(root)
    contract = create_task_contract(hr, title="Test Task")
    _git(root, "add", str(contract.relative_path))
    _git(root, "commit", "-m", "add task")
    return contract.task_id


# ── Core staged-file-aware finish behavior ──


def test_sfa_finish_commits_task_files_only(tmp_path, monkeypatch, capsys):
    """Staged-file-aware finish commits only task-finish files."""
    root = _init(tmp_path, monkeypatch)
    _create_active_task(root)

    main(["task", "finish", "--commit", "complete task",
           "--staged-file-aware", "--skip-checks", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["finished"] is True
    assert d["committed"] is True
    assert d.get("staged_file_aware") is True
    assert d.get("push_performed", False) is False
    assert d.get("backend_invocation_performed", False) is False


def test_sfa_finish_preserves_protected_staged_file(tmp_path, monkeypatch, capsys):
    """Protected staged file must remain staged after staged-file-aware finish."""
    root = _init(tmp_path, monkeypatch)
    _create_active_task(root)

    # Stage a protected file (simulating adoption-staged file)
    _write(root, "docs/PROTECTED.md", "adoption content\n")
    _git(root, "add", "docs/PROTECTED.md")
    protected_hash = _blob_hash(root, "docs/PROTECTED.md")

    main(["task", "finish", "--commit", "complete with protection",
           "--staged-file-aware", "--skip-checks", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["finished"] is True
    assert d["committed"] is True
    assert d.get("protected_staged_files_preserved") is True
    assert "docs/PROTECTED.md" in d.get("protected_staged_files_after", [])

    # Verify at git level
    assert "docs/PROTECTED.md" in _staged(root)
    assert _blob_hash(root, "docs/PROTECTED.md") == protected_hash


def test_sfa_finish_protected_hash_unchanged(tmp_path, monkeypatch, capsys):
    """Protected file blob hash must be identical before and after finish."""
    root = _init(tmp_path, monkeypatch)
    _create_active_task(root)

    _write(root, "protected.txt", "do not touch\n")
    _git(root, "add", "protected.txt")

    main(["task", "finish", "--commit", "safe finish",
           "--staged-file-aware", "--skip-checks", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d.get("protected_staged_files_preserved") is True
    before = d.get("protected_staged_file_hashes_before", {})
    after = d.get("protected_staged_file_hashes_after", {})
    for p in before:
        assert before[p] == after[p], f"Hash mismatch for {p}"


def test_sfa_finish_does_not_push(tmp_path, monkeypatch, capsys):
    """Staged-file-aware finish must never push or invoke backend."""
    root = _init(tmp_path, monkeypatch)
    _create_active_task(root)

    main(["task", "finish", "--commit", "no push",
           "--staged-file-aware", "--skip-checks", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d.get("push_performed", False) is False
    assert d.get("backend_invocation_performed", False) is False
    assert d.get("runner_execute_performed", False) is False
    assert d.get("execution_authorized", False) is False


def test_sfa_finish_without_commit_flag(tmp_path, monkeypatch, capsys):
    """--staged-file-aware without --commit just finishes normally."""
    root = _init(tmp_path, monkeypatch)
    _create_active_task(root)

    main(["task", "finish", "--staged-file-aware", "--skip-checks", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["finished"] is True
    assert d.get("committed") is None or d.get("committed") is False


# ── Simulated adoption scenario ──


def test_sfa_finish_simulated_adoption(tmp_path, monkeypatch, capsys):
    """Simulate 77S: protected adoption file staged, task finishes without including it."""
    root = _init(tmp_path, monkeypatch)
    _create_active_task(root)

    # Simulate adoption-staged file
    _write(root, "docs/REAL_CAPTURED_TASKS.md", "backend-created content\n")
    _git(root, "add", "-f", "docs/REAL_CAPTURED_TASKS.md")
    adoption_hash = _blob_hash(root, "docs/REAL_CAPTURED_TASKS.md")

    main(["task", "finish", "--commit", "Complete task safely",
           "--staged-file-aware", "--skip-checks", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["finished"] is True
    assert d["committed"] is True
    assert d.get("protected_staged_files_preserved") is True
    assert "docs/REAL_CAPTURED_TASKS.md" in d.get("protected_staged_files_after", [])

    # Verify adoption file still staged with same blob
    assert "docs/REAL_CAPTURED_TASKS.md" in _staged(root)
    assert _blob_hash(root, "docs/REAL_CAPTURED_TASKS.md") == adoption_hash

    # Verify the commit did NOT include the adoption file
    cf = subprocess.run(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"],
                        cwd=root, capture_output=True, text=True)
    committed_files = [l for l in cf.stdout.strip().split("\n") if l]
    assert "docs/REAL_CAPTURED_TASKS.md" not in committed_files


# ── Edge cases ──


def test_sfa_finish_no_active_task(tmp_path, monkeypatch, capsys):
    """Must handle no active task cleanly."""
    root = _init(tmp_path, monkeypatch)
    exit_code = main(["task", "finish", "--commit", "nothing",
                       "--staged-file-aware", "--skip-checks", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["finished"] is False
    assert exit_code == 1


def test_sfa_finish_allows_pre_existing_changes(tmp_path, monkeypatch, capsys):
    """Unlike normal --commit, --staged-file-aware allows pre-existing staged files."""
    root = _init(tmp_path, monkeypatch)
    _create_active_task(root)

    # Stage a file (would block normal --commit)
    _write(root, "extra.txt", "extra\n")
    _git(root, "add", "extra.txt")

    main(["task", "finish", "--commit", "finish with staged",
           "--staged-file-aware", "--skip-checks", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["finished"] is True
    assert d["committed"] is True
    assert d.get("protected_staged_files_preserved") is True


def test_normal_finish_still_blocks_pre_existing_changes(tmp_path, monkeypatch, capsys):
    """Normal --commit (without --staged-file-aware) still blocks on pre-existing changes."""
    root = _init(tmp_path, monkeypatch)
    _create_active_task(root)

    _write(root, "extra.txt", "extra\n")
    _git(root, "add", "extra.txt")

    exit_code = main(["task", "finish", "--commit", "should block", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d.get("finished") is False or d.get("committed") is False
    assert exit_code == 1
