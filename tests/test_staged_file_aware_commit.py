"""Tests for staged-file-aware implementation commit (Phase 79A).

Tests that pcae commit implementation commits only explicit paths
while preserving unrelated pre-existing staged files.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.paths import HarnessPath


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


# ── Basic commit behavior ──


def test_commits_only_explicit_path(tmp_path, monkeypatch, capsys):
    """Commit only the explicitly requested path (command stages it)."""
    root = _init(tmp_path, monkeypatch)
    _write(root, "impl.py", "implementation\n")
    # Do NOT pre-stage: the command stages requested paths itself
    main(["commit", "implementation", "--message", "test commit", "--path", "impl.py", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["staged_file_aware_commit_status"] == "committed"
    assert d["commit_created"] is True
    assert "impl.py" in d["committed_files"]
    assert d["push_performed"] is False


def test_preserves_protected_staged_file(tmp_path, monkeypatch, capsys):
    """Pre-existing staged file must remain staged after implementation commit."""
    root = _init(tmp_path, monkeypatch)
    _write(root, "docs/PROTECTED.md", "protected content\n")
    _git(root, "add", "docs/PROTECTED.md")
    protected_hash = _blob_hash(root, "docs/PROTECTED.md")

    _write(root, "src/impl.py", "implementation\n")
    # Do NOT pre-stage impl: the command stages it

    main(["commit", "implementation", "--message", "impl only", "--path", "src/impl.py", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["staged_file_aware_commit_status"] == "committed"
    assert d["protected_staged_files_preserved"] is True
    assert "docs/PROTECTED.md" in d["protected_staged_files_after"]
    assert "docs/PROTECTED.md" not in d["committed_files"]

    # Verify protected file is still staged with same hash
    after_staged = _staged(root)
    assert "docs/PROTECTED.md" in after_staged
    assert _blob_hash(root, "docs/PROTECTED.md") == protected_hash


def test_protected_hash_unchanged(tmp_path, monkeypatch, capsys):
    """Protected file blob hash must be identical before and after commit."""
    root = _init(tmp_path, monkeypatch)
    _write(root, "protected.txt", "do not touch\n")
    _git(root, "add", "protected.txt")

    _write(root, "change.txt", "changed\n")

    main(["commit", "implementation", "--message", "change only", "--path", "change.txt", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["staged_file_aware_commit_status"] == "committed"
    before = d["protected_staged_file_hashes_before"]
    after = d["protected_staged_file_hashes_after"]
    for p in before:
        assert before[p] == after[p], f"Hash mismatch for {p}"


def test_blocks_no_paths(tmp_path, monkeypatch, capsys):
    """Must block when no paths are provided."""
    _init(tmp_path, monkeypatch)
    exit_code = main(["commit", "implementation", "--message", "empty", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["staged_file_aware_commit_status"] == "no_paths_provided"
    assert d["commit_created"] is False
    assert exit_code == 1


def test_blocks_protected_staged_file_inclusion(tmp_path, monkeypatch, capsys):
    """Must block if requested path is a pre-existing staged file."""
    root = _init(tmp_path, monkeypatch)
    _write(root, "docs/REAL_CAPTURED_TASKS.md", "backend output\n")
    _git(root, "add", "docs/REAL_CAPTURED_TASKS.md")

    exit_code = main(["commit", "implementation", "--message", "bad commit",
                       "--path", "docs/REAL_CAPTURED_TASKS.md", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["staged_file_aware_commit_status"] == "protected_staged_file_conflict"
    assert d["commit_created"] is False
    assert exit_code == 1

    # Protected file must still be staged
    assert "docs/REAL_CAPTURED_TASKS.md" in _staged(root)


# ── Dry-run behavior ──


def test_dry_run_does_not_commit(tmp_path, monkeypatch, capsys):
    """Dry-run must not create a commit."""
    root = _init(tmp_path, monkeypatch)
    _write(root, "impl.py", "implementation\n")

    head_before = _git(root, "rev-parse", "HEAD").stdout.strip()
    main(["commit", "implementation", "--dry-run", "--message", "test", "--path", "impl.py", "--json"])
    d = json.loads(capsys.readouterr().out)
    head_after = _git(root, "rev-parse", "HEAD").stdout.strip()

    assert d["staged_file_aware_commit_status"] == "ready"
    assert d["commit_outcome"] == "dry_run"
    assert d["commit_created"] is False
    assert head_before == head_after


def test_dry_run_does_not_alter_staged(tmp_path, monkeypatch, capsys):
    """Dry-run must not alter the index."""
    root = _init(tmp_path, monkeypatch)
    _write(root, "protected.txt", "safe\n")
    _git(root, "add", "protected.txt")
    staged_before = _staged(root)

    _write(root, "impl.py", "implementation\n")
    main(["commit", "implementation", "--dry-run", "--message", "test", "--path", "impl.py", "--json"])
    capsys.readouterr()

    staged_after = _staged(root)
    assert staged_before == staged_after


# ── Safety invariants ──


def test_does_not_push(tmp_path, monkeypatch, capsys):
    """Command must never push."""
    root = _init(tmp_path, monkeypatch)
    _write(root, "impl.py", "implementation\n")
    main(["commit", "implementation", "--message", "test", "--path", "impl.py", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["push_performed"] is False
    assert d["backend_invocation_performed"] is False
    assert d["runner_execute_performed"] is False
    assert d["execution_authorized"] is False


def test_commit_result_reports_accurately(tmp_path, monkeypatch, capsys):
    """Committed files and protected files must be accurately reported."""
    root = _init(tmp_path, monkeypatch)
    _write(root, "protected.txt", "protected\n")
    _git(root, "add", "protected.txt")
    _write(root, "a.py", "a\n")
    _write(root, "b.py", "b\n")

    main(["commit", "implementation", "--message", "multi",
           "--path", "a.py", "--path", "b.py", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["staged_file_aware_commit_status"] == "committed"
    assert set(d["committed_files"]) == {"a.py", "b.py"}
    assert "protected.txt" in d["protected_staged_files_before"]
    assert "protected.txt" in d["protected_staged_files_after"]
    assert "protected.txt" not in d["committed_files"]


# ── Real-world simulation ──


def test_simulated_adoption_scenario(tmp_path, monkeypatch, capsys):
    """Simulate the 77S scenario: protected adoption file + implementation commit."""
    root = _init(tmp_path, monkeypatch)

    # Simulate: backend-created file is staged (like after 77Q adoption execution)
    _write(root, "docs/REAL_CAPTURED_TASKS.md", "backend-created content\n")
    _git(root, "add", "-f", "docs/REAL_CAPTURED_TASKS.md")
    adoption_hash = _blob_hash(root, "docs/REAL_CAPTURED_TASKS.md")

    # Implementation files changed
    _write(root, "src/pcae/commands/phase.py", "# implementation\n")
    _write(root, "src/pcae/cli.py", "# cli change\n")

    main(["commit", "implementation", "--message", "Implement Phase 77S",
           "--path", "src/pcae/commands/phase.py",
           "--path", "src/pcae/cli.py", "--json"])
    d = json.loads(capsys.readouterr().out)

    assert d["staged_file_aware_commit_status"] == "committed"
    assert d["commit_created"] is True
    assert d["protected_staged_files_preserved"] is True
    assert "docs/REAL_CAPTURED_TASKS.md" not in d["committed_files"]
    assert "docs/REAL_CAPTURED_TASKS.md" in d["protected_staged_files_after"]
    assert set(d["committed_files"]) == {"src/pcae/cli.py", "src/pcae/commands/phase.py"}

    # Verify adoption file still staged with same blob
    assert "docs/REAL_CAPTURED_TASKS.md" in _staged(root)
    assert _blob_hash(root, "docs/REAL_CAPTURED_TASKS.md") == adoption_hash
