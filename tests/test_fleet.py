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


def test_fleet_remove_deletes_registered_repo(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo)
    write_fleet_registry(tmp_path, [repo.resolve().as_posix()])
    monkeypatch.chdir(tmp_path)

    exit_code = main(["fleet", "remove", str(repo)])

    output = capsys.readouterr().out
    data = json.loads((tmp_path / ".pcae" / "fleet.json").read_text())
    assert exit_code == 0
    assert f"Removed fleet repo: {repo.resolve().as_posix()}" in output
    assert data == {"repos": []}


def test_fleet_remove_unknown_repo_fails_clearly(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    repo = tmp_path / "repo"
    unknown = tmp_path / "unknown"
    repo.mkdir()
    init_git_repo(repo)
    write_fleet_registry(tmp_path, [repo.resolve().as_posix()])
    monkeypatch.chdir(tmp_path)

    exit_code = main(["fleet", "remove", str(unknown)])

    output = capsys.readouterr().out
    data = json.loads((tmp_path / ".pcae" / "fleet.json").read_text())
    assert exit_code == 1
    assert f"Fleet repo is not registered: {unknown.resolve().as_posix()}" in output
    assert data == {"repos": [repo.resolve().as_posix()]}


def test_fleet_remove_missing_only_preserves_existing_path(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo)
    write_fleet_registry(tmp_path, [repo.resolve().as_posix()])
    monkeypatch.chdir(tmp_path)

    exit_code = main(["fleet", "remove", str(repo), "--missing-only"])

    output = capsys.readouterr().out
    data = json.loads((tmp_path / ".pcae" / "fleet.json").read_text())
    assert exit_code == 0
    assert f"Fleet repo still exists; not removed: {repo.resolve().as_posix()}" in output
    assert data == {"repos": [repo.resolve().as_posix()]}


def test_fleet_remove_missing_only_removes_missing_path(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    missing = tmp_path / "missing"
    write_fleet_registry(tmp_path, [missing.resolve().as_posix()])
    monkeypatch.chdir(tmp_path)

    exit_code = main(["fleet", "remove", str(missing), "--missing-only"])

    output = capsys.readouterr().out
    data = json.loads((tmp_path / ".pcae" / "fleet.json").read_text())
    assert exit_code == 0
    assert f"Removed fleet repo: {missing.resolve().as_posix()}" in output
    assert data == {"repos": []}


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


def test_fleet_inspect_reports_registered_repo_readiness(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    repo = tmp_path / "repo"
    init_healthy_repo(repo)
    write_fleet_registry(tmp_path, [repo.resolve().as_posix()])
    monkeypatch.chdir(tmp_path)

    exit_code = main(["fleet", "inspect"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Fleet inspection" in output
    assert "Overall status: ready" in output
    assert "Repos: 1" in output
    assert "Ready: 1" in output
    assert "Not ready: 0" in output
    assert f"Repo: {repo.resolve().as_posix()}" in output
    assert "Status: ready" in output
    assert "PCAE files: 9 present, 0 missing" in output
    assert "Policy exists: yes" in output
    assert "Hooks exist: yes" in output
    assert "Active tasks exist: yes" in output


def test_fleet_inspect_json_reports_registered_repo_readiness(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    repo = tmp_path / "repo"
    init_healthy_repo(repo)
    write_fleet_registry(tmp_path, [repo.resolve().as_posix()])
    monkeypatch.chdir(tmp_path)

    exit_code = main(["fleet", "inspect", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["overall_status"] == "ready"
    assert data["repo_count"] == 1
    assert data["ready_count"] == 1
    assert data["not_ready_count"] == 0
    assert data["repos"][0] == {
        "active_tasks_exist": True,
        "details": "ok",
        "hooks_exist": True,
        "path": repo.resolve().as_posix(),
        "pcae_files_missing": 0,
        "pcae_files_present": 9,
        "policy_exists": True,
        "status": "ready",
    }


def test_fleet_inspect_reports_missing_repo_without_crashing(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    missing = tmp_path / "missing"
    write_fleet_registry(tmp_path, [missing.as_posix()])
    monkeypatch.chdir(tmp_path)

    exit_code = main(["fleet", "inspect"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Overall status: not_ready" in output
    assert "Not ready: 1" in output
    assert f"Repo: {missing.as_posix()}" in output
    assert "PCAE files: unknown" in output
    assert f"Details: Target repo path does not exist: {missing}" in output


def test_fleet_inspect_reports_non_git_repo_without_crashing(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_fleet_registry(tmp_path, [repo.as_posix()])
    monkeypatch.chdir(tmp_path)

    exit_code = main(["fleet", "inspect", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["overall_status"] == "not_ready"
    assert data["repo_count"] == 1
    assert data["ready_count"] == 0
    assert data["not_ready_count"] == 1
    assert data["repos"][0]["status"] == "not_ready"
    assert data["repos"][0]["details"] == f"Target path is not a Git repo: {repo}"


def test_fleet_drift_reports_no_drift_for_matching_repos(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    alpha = tmp_path / "alpha"
    beta = tmp_path / "beta"
    init_healthy_repo(alpha)
    init_healthy_repo(beta)
    write_fleet_registry(
        tmp_path,
        [alpha.resolve().as_posix(), beta.resolve().as_posix()],
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["fleet", "drift"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Fleet drift" in output
    assert "Overall status: no_drift" in output
    assert "Repos: 2" in output
    assert "No governance drift detected." in output


def test_fleet_drift_json_reports_no_drift(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    repo = tmp_path / "repo"
    init_healthy_repo(repo)
    write_fleet_registry(tmp_path, [repo.resolve().as_posix()])
    monkeypatch.chdir(tmp_path)

    exit_code = main(["fleet", "drift", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data == {
        "drift_detected": False,
        "drift_findings": [],
        "overall_status": "no_drift",
        "repo_count": 1,
    }


def test_fleet_drift_reports_policy_existence_mismatch(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    alpha = tmp_path / "alpha"
    beta = tmp_path / "beta"
    init_healthy_repo(alpha)
    init_healthy_repo(beta)
    beta.joinpath(".pcae", "policy.toml").unlink()
    write_fleet_registry(
        tmp_path,
        [alpha.resolve().as_posix(), beta.resolve().as_posix()],
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["fleet", "drift", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["overall_status"] == "drift"
    assert data["drift_detected"] is True
    finding_types = {finding["type"] for finding in data["drift_findings"]}
    assert "policy_existence_mismatch" in finding_types


def test_fleet_drift_reports_hook_existence_mismatch(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    alpha = tmp_path / "alpha"
    beta = tmp_path / "beta"
    init_healthy_repo(alpha)
    init_healthy_repo(beta)
    beta.joinpath(".githooks", "pre-commit").unlink()
    write_fleet_registry(
        tmp_path,
        [alpha.resolve().as_posix(), beta.resolve().as_posix()],
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["fleet", "drift", "--json"])

    data = json.loads(capsys.readouterr().out)
    finding_types = {finding["type"] for finding in data["drift_findings"]}
    assert exit_code == 1
    assert "hook_existence_mismatch" in finding_types
    assert "missing_pcae_files" in finding_types


def test_fleet_drift_reports_enforcement_mode_mismatch(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    alpha = tmp_path / "alpha"
    beta = tmp_path / "beta"
    init_healthy_repo(alpha)
    init_healthy_repo(beta)
    policy = beta / ".pcae" / "policy.toml"
    policy.write_text(
        policy.read_text(encoding="utf-8").replace(
            'mode = "advisory"',
            'mode = "strict"',
        ),
        encoding="utf-8",
    )
    write_fleet_registry(
        tmp_path,
        [alpha.resolve().as_posix(), beta.resolve().as_posix()],
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["fleet", "drift", "--json"])

    data = json.loads(capsys.readouterr().out)
    finding_types = {finding["type"] for finding in data["drift_findings"]}
    assert exit_code == 1
    assert "enforcement_mode_mismatch" in finding_types


def test_fleet_drift_reports_missing_and_non_git_repos(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    missing = tmp_path / "missing"
    non_git = tmp_path / "non-git"
    non_git.mkdir()
    write_fleet_registry(tmp_path, [missing.as_posix(), non_git.as_posix()])
    monkeypatch.chdir(tmp_path)

    exit_code = main(["fleet", "drift"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Overall status: drift" in output
    assert "repo_unavailable" in output
    assert f"Target repo path does not exist: {missing}" in output
    assert f"Target path is not a Git repo: {non_git}" in output


def test_fleet_apply_dry_run_reports_plan_without_writing(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo)
    write_fleet_registry(tmp_path, [repo.resolve().as_posix()])
    monkeypatch.chdir(tmp_path)

    exit_code = main(["fleet", "apply", "--dry-run"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Fleet apply dry run" in output
    assert "Overall status: ready" in output
    assert f"Repo: {repo.resolve().as_posix()}" in output
    assert "Would create:" in output
    assert ".pcae/policy.toml" in output
    assert not repo.joinpath(".pcae", "policy.toml").exists()


def test_fleet_apply_force_writes_registered_repo(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo)
    write_fleet_registry(tmp_path, [repo.resolve().as_posix()])
    monkeypatch.chdir(tmp_path)

    exit_code = main(["fleet", "apply", "--force"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Fleet apply" in output
    assert "Overall status: applied" in output
    assert repo.joinpath(".pcae", "policy.toml").is_file()
    assert repo.joinpath(".githooks", "pre-commit").is_file()
    assert repo.joinpath("tasks", "TODO.md").is_file()


def test_fleet_apply_force_respects_overwrite_boundaries(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo)
    init_harness(HarnessPath(repo))
    repo.joinpath("AGENTS.md").write_text("user memory\n", encoding="utf-8")
    repo.joinpath(".pcae", "policy.toml").write_text("old policy\n", encoding="utf-8")
    write_fleet_registry(tmp_path, [repo.resolve().as_posix()])
    monkeypatch.chdir(tmp_path)

    exit_code = main(["fleet", "apply", "--force"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Overwritten:" in output
    assert ".pcae/policy.toml" in output
    assert repo.joinpath("AGENTS.md").read_text(encoding="utf-8") == "user memory\n"
    assert "old policy" not in repo.joinpath(".pcae", "policy.toml").read_text(
        encoding="utf-8"
    )


def test_fleet_apply_requires_explicit_mode(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["fleet", "apply"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Fleet apply requires --dry-run or --force." in output


def test_fleet_apply_reports_missing_and_non_git_repos(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    missing = tmp_path / "missing"
    non_git = tmp_path / "non-git"
    non_git.mkdir()
    write_fleet_registry(tmp_path, [missing.as_posix(), non_git.as_posix()])
    monkeypatch.chdir(tmp_path)

    dry_run_exit_code = main(["fleet", "apply", "--dry-run"])
    dry_run_output = capsys.readouterr().out
    force_exit_code = main(["fleet", "apply", "--force"])
    force_output = capsys.readouterr().out

    assert dry_run_exit_code == 1
    assert force_exit_code == 1
    assert f"Target repo path does not exist: {missing}" in dry_run_output
    assert f"Target path is not a Git repo: {non_git}" in dry_run_output
    assert f"Target repo path does not exist: {missing}" in force_output
    assert f"Target path is not a Git repo: {non_git}" in force_output


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
