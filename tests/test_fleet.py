from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.fleet import write_fleet_export
from pcae.core.paths import HarnessPath
from pcae.core.session import write_session_snapshot
from pcae.core.tasks import create_task_contract


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


def test_fleet_health_reports_registered_repo(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    repo = tmp_path / "repo"
    init_healthy_repo(repo)
    write_fleet_registry(tmp_path, [repo.resolve().as_posix()])
    monkeypatch.chdir(tmp_path)

    exit_code = main(["fleet", "health"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Fleet health" in output
    assert "Overall status: healthy" in output
    assert "Repos: 1" in output
    assert "Healthy: 1" in output
    assert "Unhealthy: 0" in output
    assert f"Repo: {repo.resolve().as_posix()}" in output
    assert "Status: healthy" in output
    assert "Active task: 20260525-0800-fleet-health-task" in output
    assert "Session continuity: verified" in output
    assert "Latest enforcement mode: advisory" in output


def test_fleet_health_json_reports_registered_repo(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    repo = tmp_path / "repo"
    init_healthy_repo(repo)
    write_fleet_registry(tmp_path, [repo.resolve().as_posix()])
    monkeypatch.chdir(tmp_path)

    exit_code = main(["fleet", "health", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["overall_status"] == "healthy"
    assert data["repo_count"] == 1
    assert data["healthy_count"] == 1
    assert data["unhealthy_count"] == 0
    assert data["repos"][0]["path"] == repo.resolve().as_posix()
    assert data["repos"][0]["status"] == "healthy"
    assert data["repos"][0]["active_task"] == {
        "id": "20260525-0800-fleet-health-task",
        "title": "Fleet health task",
    }
    assert data["repos"][0]["session_continuity"] == "verified"
    assert data["repos"][0]["latest_enforcement_mode"] == "advisory"
    assert data["repos"][0]["latest_dependency_warnings"] is None


def test_fleet_health_reports_missing_repo_without_crashing(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    missing = tmp_path / "missing"
    write_fleet_registry(tmp_path, [missing.as_posix()])
    monkeypatch.chdir(tmp_path)

    exit_code = main(["fleet", "health"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Overall status: unhealthy" in output
    assert "Unhealthy: 1" in output
    assert f"Repo: {missing.as_posix()}" in output
    assert f"Details: Target repo path does not exist: {missing}" in output


def test_fleet_health_reports_non_git_repo_without_crashing(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_fleet_registry(tmp_path, [repo.as_posix()])
    monkeypatch.chdir(tmp_path)

    exit_code = main(["fleet", "health", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["overall_status"] == "unhealthy"
    assert data["repo_count"] == 1
    assert data["healthy_count"] == 0
    assert data["unhealthy_count"] == 1
    assert data["repos"][0]["status"] == "unhealthy"
    assert data["repos"][0]["details"] == f"Target path is not a Git repo: {repo}"


def test_fleet_export_writes_portable_bundle(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    repo = tmp_path / "repo"
    init_healthy_repo(repo)
    write_fleet_registry(tmp_path, [repo.resolve().as_posix()])
    monkeypatch.chdir(tmp_path)

    exit_code = main(["fleet", "export"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert (
        "Wrote fleet governance bundle: "
        ".pcae/fleet-exports/fleet-governance-bundle-"
    ) in output
    bundles = sorted((tmp_path / ".pcae" / "fleet-exports").glob("*.json"))
    assert len(bundles) == 1
    data = json.loads(bundles[0].read_text(encoding="utf-8"))
    assert data["overall_status"] == "healthy"
    assert data["repo_count"] == 1
    assert data["healthy_count"] == 1
    assert data["unhealthy_count"] == 0
    assert data["repos"][0] == {
        "active_task": {
            "id": "20260525-0800-fleet-health-task",
            "title": "Fleet health task",
        },
        "latest_dependency_warnings": None,
        "latest_enforcement_mode": "advisory",
        "path": repo.resolve().as_posix(),
        "session_continuity": "verified",
        "status": "healthy",
    }


def test_fleet_export_uses_deterministic_timestamped_filename(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    init_healthy_repo(repo)
    write_fleet_registry(tmp_path, [repo.resolve().as_posix()])

    export = write_fleet_export(
        HarnessPath(tmp_path),
        generated_at=datetime(2026, 5, 25, 9, 30, 5, tzinfo=timezone.utc),
    )

    assert export.relative_path.as_posix() == (
        ".pcae/fleet-exports/fleet-governance-bundle-20260525-093005.json"
    )
    assert export.data["generated_timestamp"] == "2026-05-25T09:30:05+00:00"
    assert (tmp_path / export.relative_path).is_file()


def test_fleet_export_includes_unhealthy_missing_repo(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing"
    write_fleet_registry(tmp_path, [missing.as_posix()])

    export = write_fleet_export(
        HarnessPath(tmp_path),
        generated_at=datetime(2026, 5, 25, 9, 31, tzinfo=timezone.utc),
    )

    assert export.data["overall_status"] == "unhealthy"
    assert export.data["repo_count"] == 1
    assert export.data["healthy_count"] == 0
    assert export.data["unhealthy_count"] == 1
    assert export.data["repos"][0]["path"] == missing.as_posix()
    assert export.data["repos"][0]["status"] == "unhealthy"


def test_fleet_export_bundles_are_gitignored(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    repo = tmp_path / "repo"
    init_healthy_repo(repo)
    write_fleet_registry(tmp_path, [repo.resolve().as_posix()])
    write_fleet_export_ignore(tmp_path)
    init_git_repo(tmp_path)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "baseline"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["fleet", "export"])

    status = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    capsys.readouterr()
    assert exit_code == 0
    assert status.stdout == ""


def init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )


def init_healthy_repo(root: Path) -> None:
    root.mkdir()
    init_git_repo(root)
    init_harness(HarnessPath(root))
    create_task_contract(
        HarnessPath(root),
        "Fleet health task",
        created_at=datetime(2026, 5, 25, 8, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(
        HarnessPath(root),
        created_at=datetime(2026, 5, 25, 8, 1, tzinfo=timezone.utc),
    )
    subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "baseline"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )


def write_fleet_registry(root: Path, repos: list[str]) -> None:
    target = root / ".pcae" / "fleet.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps({"repos": repos}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_fleet_export_ignore(root: Path) -> None:
    target = root / ".pcae" / "fleet-exports" / ".gitignore"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("fleet-governance-bundle-*.json\n", encoding="utf-8")
