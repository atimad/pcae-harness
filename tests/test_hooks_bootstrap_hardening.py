"""Tests for Phase 108E — Local Governance Bootstrap & Pre-Push Hardening.

Verifies: hook status diagnosis across every state, `pcae hooks status`
and `pcae doctor hooks`, `pcae init` auto-installing hooks, the pre-push
hook's content and safety properties, and a fresh-clone bootstrap
simulation using a real local `git clone` (no network access).

Every test uses `tmp_path` (isolated per test, pytest-xdist safe) and,
where a subprocess `pcae` invocation is needed, passes `cwd=` explicitly
rather than relying on shared process state — consistent with the
isolation pattern established in Phase 107D.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.hooks import (
    EXPECTED_HOOK_FILES,
    HOOK_STATUS_HOOK_FILES_MISSING,
    HOOK_STATUS_HOOK_FILES_NOT_EXECUTABLE,
    HOOK_STATUS_HOOKS_PATH_INCORRECT,
    HOOK_STATUS_HOOKS_PATH_MISSING,
    HOOK_STATUS_INSTALLED,
    HOOK_STATUS_NOT_A_GIT_REPO,
    HOOKS_PATH_VALUE,
    diagnose_hooks,
    install_hooks,
)
from pcae.core.paths import HarnessPath
from pcae.core.templates import INIT_TEMPLATES

REPO_ROOT = Path(__file__).resolve().parent.parent


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True,
    )


def _init_git_repo(root: Path) -> None:
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test User")


def _write_both_hooks(root: Path, executable: bool = True) -> None:
    hooks_dir = root / ".githooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    for name in EXPECTED_HOOK_FILES:
        path = hooks_dir / name
        path.write_text("#!/usr/bin/env sh\nset -eu\ntrue\n", encoding="utf-8")
        if executable:
            os.chmod(path, 0o755)


# ═══════════════════════════════════════════════════════════════════════
# diagnose_hooks() state coverage
# ═══════════════════════════════════════════════════════════════════════


def test_diagnose_hooks_not_a_git_repo(tmp_path):
    status = diagnose_hooks(HarnessPath(tmp_path))
    assert status.status == HOOK_STATUS_NOT_A_GIT_REPO
    assert status.healthy is False
    assert status.git_repo is False


def test_diagnose_hooks_hooks_path_missing(tmp_path):
    _init_git_repo(tmp_path)
    _write_both_hooks(tmp_path)
    status = diagnose_hooks(HarnessPath(tmp_path))
    assert status.status == HOOK_STATUS_HOOKS_PATH_MISSING
    assert status.healthy is False
    assert "pcae hooks install" in status.recommended_remediation[0]


def test_diagnose_hooks_hooks_path_incorrect(tmp_path):
    _init_git_repo(tmp_path)
    _write_both_hooks(tmp_path)
    _git(tmp_path, "config", "core.hooksPath", "some/other/path")
    status = diagnose_hooks(HarnessPath(tmp_path))
    assert status.status == HOOK_STATUS_HOOKS_PATH_INCORRECT
    assert status.hooks_path_configured == "some/other/path"
    assert status.healthy is False


def test_diagnose_hooks_hook_files_missing(tmp_path):
    _init_git_repo(tmp_path)
    (tmp_path / ".githooks").mkdir()
    (tmp_path / ".githooks" / "pre-commit").write_text("#!/usr/bin/env sh\ntrue\n")
    os.chmod(tmp_path / ".githooks" / "pre-commit", 0o755)
    _git(tmp_path, "config", "core.hooksPath", HOOKS_PATH_VALUE)
    status = diagnose_hooks(HarnessPath(tmp_path))
    assert status.status == HOOK_STATUS_HOOK_FILES_MISSING
    assert status.missing_hook_files == ("pre-push",)
    assert status.healthy is False
    assert "pcae init --force" in status.recommended_remediation[0]


def test_diagnose_hooks_hook_files_not_executable(tmp_path):
    _init_git_repo(tmp_path)
    _write_both_hooks(tmp_path, executable=False)
    _git(tmp_path, "config", "core.hooksPath", HOOKS_PATH_VALUE)
    status = diagnose_hooks(HarnessPath(tmp_path))
    assert status.status == HOOK_STATUS_HOOK_FILES_NOT_EXECUTABLE
    assert set(status.non_executable_hook_files) == set(EXPECTED_HOOK_FILES)
    assert "chmod +x" in status.recommended_remediation[0]


def test_diagnose_hooks_installed(tmp_path):
    _init_git_repo(tmp_path)
    _write_both_hooks(tmp_path)
    _git(tmp_path, "config", "core.hooksPath", HOOKS_PATH_VALUE)
    status = diagnose_hooks(HarnessPath(tmp_path))
    assert status.status == HOOK_STATUS_INSTALLED
    assert status.healthy is True
    assert status.missing_hook_files == ()
    assert status.non_executable_hook_files == ()
    assert status.recommended_remediation == ()


def test_diagnose_hooks_never_modifies_state(tmp_path):
    _init_git_repo(tmp_path)
    before = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if p.is_file())
    diagnose_hooks(HarnessPath(tmp_path))
    after = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if p.is_file())
    assert before == after
    assert diagnose_hooks(HarnessPath(tmp_path)).hooks_path_configured is None


# ═══════════════════════════════════════════════════════════════════════
# pcae hooks status / pcae doctor hooks commands
# ═══════════════════════════════════════════════════════════════════════


def test_hooks_status_command_reports_healthy(tmp_path, monkeypatch, capsys):
    _init_git_repo(tmp_path)
    _write_both_hooks(tmp_path)
    _git(tmp_path, "config", "core.hooksPath", HOOKS_PATH_VALUE)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["hooks", "status"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Status: installed" in output
    assert "Healthy: True" in output


def test_hooks_status_command_reports_unhealthy(tmp_path, monkeypatch, capsys):
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["hooks", "status"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Healthy: False" in output


def test_hooks_status_json_output(tmp_path, monkeypatch, capsys):
    _init_git_repo(tmp_path)
    _write_both_hooks(tmp_path)
    _git(tmp_path, "config", "core.hooksPath", HOOKS_PATH_VALUE)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["hooks", "status", "--json"])

    output = capsys.readouterr().out
    data = json.loads(output)
    assert exit_code == 0
    assert data["status"] == "installed"
    assert data["healthy"] is True


def test_doctor_hooks_command_shares_diagnosis(tmp_path, monkeypatch, capsys):
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["doctor", "hooks"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Git hook governance diagnostic" in output
    assert "pcae hooks install" in output


def test_doctor_hooks_recommends_remediation_for_missing_files(tmp_path, monkeypatch, capsys):
    _init_git_repo(tmp_path)
    (tmp_path / ".githooks").mkdir()
    (tmp_path / ".githooks" / "pre-commit").write_text("#!/usr/bin/env sh\ntrue\n")
    os.chmod(tmp_path / ".githooks" / "pre-commit", 0o755)
    _git(tmp_path, "config", "core.hooksPath", HOOKS_PATH_VALUE)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["doctor", "hooks", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["status"] == "hook_files_missing"
    assert "pre-push" in data["missing_hook_files"]


# ═══════════════════════════════════════════════════════════════════════
# pcae init auto-installs hooks
# ═══════════════════════════════════════════════════════════════════════


def test_init_auto_installs_hooks_in_git_repo(tmp_path, monkeypatch, capsys):
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["init"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Installed PCAE Git hooks" in output
    assert diagnose_hooks(HarnessPath(tmp_path)).healthy is True


def test_init_skips_hook_install_outside_git_repo(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    exit_code = main(["init"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Skipped Git hook installation: not inside a Git repository." in output


def test_init_creates_pre_push_template(tmp_path):
    init_harness(HarnessPath(tmp_path))
    pre_push = tmp_path / ".githooks" / "pre-push"
    assert pre_push.is_file()
    assert os.access(pre_push, os.X_OK)
    assert pre_push.read_text(encoding="utf-8") == INIT_TEMPLATES[Path(".githooks/pre-push")]


def test_init_dry_run_does_not_install_hooks(tmp_path, monkeypatch, capsys):
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["init", "--dry-run"])

    assert diagnose_hooks(HarnessPath(tmp_path)).hooks_path_configured is None


# ═══════════════════════════════════════════════════════════════════════
# Pre-push hook content and safety properties
# ═══════════════════════════════════════════════════════════════════════


def test_pre_push_hook_runs_expected_governance_checks():
    pre_push = REPO_ROOT / ".githooks" / "pre-push"
    content = pre_push.read_text(encoding="utf-8")
    for expected in ("pcae health", "pcae check", "pcae doctor task-memory", "pcae push check"):
        assert expected in content


def test_pre_push_hook_matches_template():
    pre_push = REPO_ROOT / ".githooks" / "pre-push"
    assert pre_push.read_text(encoding="utf-8") == INIT_TEMPLATES[Path(".githooks/pre-push")]


def test_pre_push_hook_is_executable():
    pre_push = REPO_ROOT / ".githooks" / "pre-push"
    assert os.access(pre_push, os.X_OK)


def test_pre_push_hook_never_executes_repository_code():
    content = (REPO_ROOT / ".githooks" / "pre-push").read_text(encoding="utf-8")
    forbidden = ("python ", "python3 ", "./", "sh ./", "bash ./", "eval ", "source ")
    for token in forbidden:
        assert token not in content


def test_pre_push_hook_never_invokes_permission_broker():
    content = (REPO_ROOT / ".githooks" / "pre-push").read_text(encoding="utf-8")
    assert "permission-broker" not in content
    assert "permission_broker" not in content


def test_pre_push_hook_never_mutates_repository_state():
    """None of the four commands the hook runs are mutating; confirmed by
    the absence of any git-mutating or file-writing subcommand name.
    ('push check' is expected and read-only; a bare 'pcae push' or 'git
    push' invocation would not be.)"""
    content = (REPO_ROOT / ".githooks" / "pre-push").read_text(encoding="utf-8")
    forbidden = ("commit", "git push", "task new", "task finish", "--fix", "--force")
    for token in forbidden:
        assert token not in content
    assert "pcae push\n" not in content
    assert "pcae push check" in content


def test_pre_push_hook_blocks_push_on_governance_failure(tmp_path, monkeypatch):
    """Run the real pre-push script against an ungoverned repo (no active
    task, but otherwise healthy) — since this repo itself is healthy at
    baseline, simulate failure via a repo with no PCAE scaffold at all,
    which must fail pcae health and therefore exit non-zero."""
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    pre_push = REPO_ROOT / ".githooks" / "pre-push"

    result = subprocess.run(
        ["sh", str(pre_push)], cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode != 0


# ═══════════════════════════════════════════════════════════════════════
# Fresh-clone bootstrap validation (local clone, no network)
# ═══════════════════════════════════════════════════════════════════════


def test_fresh_clone_bootstrap_reaches_governed_state(tmp_path):
    """Simulate the full documented onboarding journey: create a minimal
    upstream repo, clone it locally, run `pcae init` in the clone, and
    confirm hooks become active without any additional manual step."""
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    _init_git_repo(upstream)
    init_harness(HarnessPath(upstream))
    _git(upstream, "add", ".")
    _git(upstream, "commit", "-q", "-m", "baseline")

    clone = tmp_path / "clone"
    subprocess.run(
        ["git", "clone", "-q", str(upstream), str(clone)],
        capture_output=True, text=True, check=True,
    )

    # Fresh clone: hooks are tracked files, but core.hooksPath is a local
    # git-config setting that is never cloned — must start ungoverned.
    pre_status = diagnose_hooks(HarnessPath(clone))
    assert pre_status.healthy is False
    assert pre_status.status == HOOK_STATUS_HOOKS_PATH_MISSING

    # Documented bootstrap: `pcae init` (idempotent; auto-installs hooks).
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "init"],
        cwd=clone, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0
    assert "Installed PCAE Git hooks" in result.stdout

    post_status = diagnose_hooks(HarnessPath(clone))
    assert post_status.healthy is True
    assert post_status.status == HOOK_STATUS_INSTALLED


def test_fresh_clone_hooks_status_reports_healthy_after_bootstrap(tmp_path):
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    _init_git_repo(upstream)
    init_harness(HarnessPath(upstream))
    _git(upstream, "add", ".")
    _git(upstream, "commit", "-q", "-m", "baseline")

    clone = tmp_path / "clone"
    subprocess.run(
        ["git", "clone", "-q", str(upstream), str(clone)],
        capture_output=True, text=True, check=True,
    )
    subprocess.run(
        [sys.executable, "-m", "pcae", "init"],
        cwd=clone, capture_output=True, text=True, check=True, timeout=30,
    )

    status_result = subprocess.run(
        [sys.executable, "-m", "pcae", "hooks", "status", "--json"],
        cwd=clone, capture_output=True, text=True, timeout=30,
    )
    data = json.loads(status_result.stdout)
    assert status_result.returncode == 0
    assert data["healthy"] is True
