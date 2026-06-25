"""Tests for staged-file-aware pcae push (Phase 79C).

Tests that pcae push --staged-file-aware pushes approved commits while
preserving unrelated pre-existing staged files.

Uses local bare remotes for push testing without network access.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

pytestmark = [pytest.mark.slow, pytest.mark.integration]

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.paths import HarnessPath


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True)


def _write(root: Path, rel: str, content: str = "content\n") -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def _staged(root: Path) -> list[str]:
    r = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=root, capture_output=True, text=True)
    return [l for l in r.stdout.strip().split("\n") if l]


def _blob_hash(root: Path, path: str) -> str:
    r = subprocess.run(["git", "rev-parse", f":0:{path}"], cwd=root, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def _init_with_remote(tmp_path: Path, monkeypatch) -> tuple[Path, Path]:
    """Create a PCAE repo with a local bare remote for push testing."""
    bare = tmp_path / "remote.git"
    bare.mkdir()
    subprocess.run(["git", "init", "--bare"], cwd=bare, check=True, capture_output=True)

    work = tmp_path / "work"
    work.mkdir()
    init_harness(HarnessPath(work))
    subprocess.run(["git", "init"], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "remote", "add", "origin", str(bare)], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=work, check=True, capture_output=True)
    # Rename branch to main if needed
    r = subprocess.run(["git", "branch", "-M", "main"], cwd=work, capture_output=True, text=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], cwd=work, check=True, capture_output=True)
    monkeypatch.chdir(work)
    return work, bare


def _create_unpushed_commit(root: Path, filename: str = "impl.py", msg: str = "implementation") -> str:
    _write(root, filename, f"# {msg}\n")
    _git(root, "add", filename)
    _git(root, "commit", "-m", msg, "--", filename)
    return _git(root, "rev-parse", "HEAD").stdout.strip()


# ── Core staged-file-aware push behavior ──


def test_sfa_push_with_no_staged_files(tmp_path, monkeypatch, capsys):
    """Push succeeds when no protected staged files exist."""
    work, _ = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)

    main(["push", "--staged-file-aware", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["push_staged_file_aware_status"] == "pushed"
    assert d["push_outcome"] == "pushed"
    assert d["force_push_performed"] is False
    assert d["raw_git_push_performed"] is False


def test_sfa_push_preserves_protected_staged_file(tmp_path, monkeypatch, capsys):
    """Protected staged file must remain staged after push."""
    work, _ = _init_with_remote(tmp_path, monkeypatch)

    # Stage a protected file
    _write(work, "docs/PROTECTED.md", "adoption content\n")
    _git(work, "add", "docs/PROTECTED.md")
    protected_hash = _blob_hash(work, "docs/PROTECTED.md")

    # Create an unrelated unpushed commit
    _create_unpushed_commit(work)

    main(["push", "--staged-file-aware", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["push_staged_file_aware_status"] == "pushed"
    assert d["protected_staged_files_preserved"] is True
    assert "docs/PROTECTED.md" in d["protected_staged_files_after"]

    # Verify at git level
    assert "docs/PROTECTED.md" in _staged(work)
    assert _blob_hash(work, "docs/PROTECTED.md") == protected_hash


def test_sfa_push_protected_hash_unchanged(tmp_path, monkeypatch, capsys):
    """Protected file blob hash must be identical before and after push."""
    work, _ = _init_with_remote(tmp_path, monkeypatch)

    _write(work, "protected.txt", "do not touch\n")
    _git(work, "add", "protected.txt")

    _create_unpushed_commit(work)

    main(["push", "--staged-file-aware", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["protected_staged_files_preserved"] is True
    before = d["protected_staged_file_hashes_before"]
    after = d["protected_staged_file_hashes_after"]
    for p in before:
        assert before[p] == after[p], f"Hash mismatch for {p}"


def test_sfa_push_blocks_protected_file_in_commits(tmp_path, monkeypatch, capsys):
    """Must block if protected staged file appears in unpushed commit range."""
    work, _ = _init_with_remote(tmp_path, monkeypatch)

    # Create a commit that includes the file
    _write(work, "docs/PROTECTED.md", "committed content\n")
    _git(work, "add", "docs/PROTECTED.md")
    _git(work, "commit", "-m", "add protected")

    # Stage the same file again (modified) as protected
    _write(work, "docs/PROTECTED.md", "adoption content\n")
    _git(work, "add", "docs/PROTECTED.md")

    exit_code = main(["push", "--staged-file-aware", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["push_staged_file_aware_status"] == "protected_file_in_unpushed_commits"
    assert d["push_outcome"] == "blocked"
    assert exit_code == 1
    assert "docs/PROTECTED.md" in d["protected_file_in_unpushed_commits"]


def test_sfa_push_nothing_to_push(tmp_path, monkeypatch, capsys):
    """Reports nothing_to_push when no unpushed commits exist."""
    work, _ = _init_with_remote(tmp_path, monkeypatch)

    main(["push", "--staged-file-aware", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["push_staged_file_aware_status"] == "nothing_to_push"
    assert d["push_outcome"] == "nothing_to_push"


# ── Dry-run/check behavior ──


def test_sfa_push_dry_run_does_not_push(tmp_path, monkeypatch, capsys):
    """Dry-run must not actually push."""
    work, _ = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)

    # Count unpushed before
    before = int(_git(work, "rev-list", "--count", "origin/main..HEAD").stdout.strip())

    main(["push", "--staged-file-aware", "--dry-run", "--json"])
    d = json.loads(capsys.readouterr().out)

    after = int(_git(work, "rev-list", "--count", "origin/main..HEAD").stdout.strip())
    assert d["push_outcome"] == "dry_run"
    assert before == after


def test_sfa_push_dry_run_reports_protected_files(tmp_path, monkeypatch, capsys):
    """Dry-run must report protected staged files."""
    work, _ = _init_with_remote(tmp_path, monkeypatch)
    _write(work, "protected.txt", "safe\n")
    _git(work, "add", "protected.txt")
    _create_unpushed_commit(work)

    main(["push", "--staged-file-aware", "--dry-run", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert "protected.txt" in d["protected_staged_files_before"]
    assert d["push_outcome"] == "dry_run"


# ── Safety invariants ──


def test_sfa_push_no_backend_no_runner(tmp_path, monkeypatch, capsys):
    """Command must never invoke backend or runner."""
    work, _ = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)

    main(["push", "--staged-file-aware", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["backend_invocation_performed"] is False
    assert d["runner_execute_performed"] is False
    assert d["execution_authorized"] is False
    assert d["force_push_performed"] is False
    assert d["raw_git_push_performed"] is False


def test_sfa_push_simulated_adoption(tmp_path, monkeypatch, capsys):
    """Simulate: protected adoption file staged + push implementation commits."""
    work, _ = _init_with_remote(tmp_path, monkeypatch)

    # Stage adoption file (simulating 77Q result)
    _write(work, "docs/REAL_CAPTURED_TASKS.md", "backend-created content\n")
    _git(work, "add", "-f", "docs/REAL_CAPTURED_TASKS.md")
    adoption_hash = _blob_hash(work, "docs/REAL_CAPTURED_TASKS.md")

    # Create unrelated implementation commit
    _create_unpushed_commit(work, "src/impl.py", "Phase 77R implementation")

    main(["push", "--staged-file-aware", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["push_staged_file_aware_status"] == "pushed"
    assert d["protected_staged_files_preserved"] is True
    assert "docs/REAL_CAPTURED_TASKS.md" in d["protected_staged_files_after"]

    # Verify adoption file still staged with same blob
    assert "docs/REAL_CAPTURED_TASKS.md" in _staged(work)
    assert _blob_hash(work, "docs/REAL_CAPTURED_TASKS.md") == adoption_hash


def test_normal_push_unchanged(tmp_path, monkeypatch, capsys):
    """Normal push (without --staged-file-aware) retains existing behavior."""
    work, _ = _init_with_remote(tmp_path, monkeypatch)

    # Normal push with nothing to push should return nothing_to_push
    main(["push", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d.get("mode") == "nothing_to_push"
    assert "push_staged_file_aware_status" not in d
