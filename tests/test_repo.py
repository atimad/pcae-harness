from __future__ import annotations

import json
from pathlib import Path
import subprocess

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.paths import HarnessPath


def test_repo_trial_dry_run_reports_target_state(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    target = tmp_path / "target"
    target.mkdir()
    init_git_repo(target)
    (target / "AGENTS.md").write_text("custom\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["repo", "trial", str(target), "--dry-run"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "PCAE repo trial" in output
    assert f"Target repo: {target}" in output
    assert "PCAE files: 1 present, 8 missing" in output
    assert "Policy exists: no" in output
    assert "Active tasks exist: no" in output
    assert "Hooks exist: no" in output
    assert "pcae init would create:" in output
    assert "  PROJECT_STATUS.md" in output
    assert "pcae init would skip:" in output
    assert "  AGENTS.md" in output


def test_repo_trial_reports_existing_pcae_files(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    target = tmp_path / "target"
    target.mkdir()
    init_git_repo(target)
    init_harness(HarnessPath(target))
    (target / "tasks" / "active").mkdir()
    (target / "tasks" / "active" / "20260525-0800-task.md").write_text(
        "# Task\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["repo", "trial", str(target), "--dry-run"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "PCAE files: 9 present, 0 missing" in output
    assert "Policy exists: yes" in output
    assert "Active tasks exist: yes" in output
    assert "Hooks exist: yes" in output
    assert "pcae init would create:" in output
    assert "  none" in output


def test_repo_trial_json_reports_target_state(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    target = tmp_path / "target"
    target.mkdir()
    init_git_repo(target)
    (target / "AGENTS.md").write_text("custom\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["repo", "trial", str(target), "--dry-run", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["target_repo"] == target.as_posix()
    assert data["is_git_repo"] is True
    assert data["pcae_files_present"] == 1
    assert data["pcae_files_missing"] == 8
    assert data["policy_exists"] is False
    assert data["active_tasks_exist"] is False
    assert data["hooks_exist"] is False
    assert "PROJECT_STATUS.md" in data["init_would_create"]
    assert "AGENTS.md" in data["init_would_skip"]


def test_repo_trial_missing_path_fails_clearly(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    missing = tmp_path / "missing"
    monkeypatch.chdir(tmp_path)

    exit_code = main(["repo", "trial", str(missing), "--dry-run"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert f"Target repo path does not exist: {missing}" in output


def test_repo_trial_non_git_path_fails_clearly(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    target = tmp_path / "target"
    target.mkdir()
    monkeypatch.chdir(tmp_path)

    exit_code = main(["repo", "trial", str(target), "--dry-run"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert f"Target path is not a Git repo: {target}" in output


def test_repo_trial_requires_dry_run(tmp_path: Path, monkeypatch, capsys) -> None:
    target = tmp_path / "target"
    target.mkdir()
    init_git_repo(target)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["repo", "trial", str(target)])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Repo trial only supports --dry-run." in output


def test_repo_trial_dry_run_writes_nothing(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    target = tmp_path / "target"
    target.mkdir()
    init_git_repo(target)
    before = text_file_snapshot(target)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["repo", "trial", str(target), "--dry-run"])

    after = text_file_snapshot(target)
    capsys.readouterr()
    assert exit_code == 0
    assert after == before


def init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)


def text_file_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(root).parts
    }
