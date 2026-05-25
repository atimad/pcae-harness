from __future__ import annotations

import json
from pathlib import Path
import subprocess

from pcae.cli import main


def test_fleet_add_registers_absolute_repo_path(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["fleet", "add", str(repo)])

    output = capsys.readouterr().out
    data = json.loads((tmp_path / ".pcae" / "fleet.json").read_text())
    assert exit_code == 0
    assert f"Added fleet repo: {repo.resolve().as_posix()}" in output
    assert data == {"repos": [repo.resolve().as_posix()]}


def test_fleet_add_does_not_duplicate_repo(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo)
    monkeypatch.chdir(tmp_path)

    first_exit_code = main(["fleet", "add", str(repo)])
    capsys.readouterr()
    second_exit_code = main(["fleet", "add", str(repo)])

    output = capsys.readouterr().out
    data = json.loads((tmp_path / ".pcae" / "fleet.json").read_text())
    assert first_exit_code == 0
    assert second_exit_code == 0
    assert f"Fleet repo already registered: {repo.resolve().as_posix()}" in output
    assert data == {"repos": [repo.resolve().as_posix()]}


def test_fleet_list_prints_registered_repos(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo)
    monkeypatch.chdir(tmp_path)
    main(["fleet", "add", str(repo)])
    capsys.readouterr()

    exit_code = main(["fleet", "list"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Fleet repos:" in output
    assert f"  {repo.resolve().as_posix()}" in output


def test_fleet_list_handles_empty_registry(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["fleet", "list"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Fleet repos:" in output
    assert "  none" in output


def test_fleet_add_missing_path_fails_clearly(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    missing = tmp_path / "missing"
    monkeypatch.chdir(tmp_path)

    exit_code = main(["fleet", "add", str(missing)])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert f"Target repo path does not exist: {missing}" in output
    assert not (tmp_path / ".pcae" / "fleet.json").exists()


def test_fleet_add_non_git_path_fails_clearly(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.chdir(tmp_path)

    exit_code = main(["fleet", "add", str(repo)])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert f"Target path is not a Git repo: {repo}" in output
    assert not (tmp_path / ".pcae" / "fleet.json").exists()


def test_fleet_registry_is_sorted_and_readable(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    beta = tmp_path / "beta"
    alpha = tmp_path / "alpha"
    beta.mkdir()
    alpha.mkdir()
    init_git_repo(beta)
    init_git_repo(alpha)
    monkeypatch.chdir(tmp_path)

    main(["fleet", "add", str(beta)])
    main(["fleet", "add", str(alpha)])

    capsys.readouterr()
    content = (tmp_path / ".pcae" / "fleet.json").read_text(encoding="utf-8")
    data = json.loads(content)
    assert content.endswith("\n")
    assert data == {
        "repos": [
            alpha.resolve().as_posix(),
            beta.resolve().as_posix(),
        ]
    }


def init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
