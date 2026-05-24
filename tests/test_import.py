from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.export import write_governance_export_bundle
from pcae.core.paths import HarnessPath
from pcae.core.session import write_session_snapshot
from pcae.core.tasks import create_task_contract


def test_import_bundle_dry_run_previews_generated_bundle(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_ready_repo(tmp_path)
    write_session_snapshot(
        HarnessPath(tmp_path),
        created_at=datetime(2026, 5, 24, 8, 0, tzinfo=timezone.utc),
    )
    commit_baseline(tmp_path)
    bundle = write_governance_export_bundle(
        HarnessPath(tmp_path),
        generated_at=datetime(2026, 5, 24, 9, 0, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["import", "bundle", bundle.relative_path.as_posix(), "--dry-run"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Governance bundle import preview" in output
    assert "Bundle timestamp: 2026-05-24T09:00:00+00:00" in output
    assert "Active task: 20260524-0800-import-task" in output
    assert "Title: Import task" in output
    assert "Session snapshot: available" in output
    assert "Health status: healthy" in output
    assert "Check status: passed" in output
    assert "Architecture metrics: missing" in output
    assert "Policy summary: available" in output
    assert "  .pcae/session.json" in output
    assert "  .pcae/architecture-history.json" in output
    assert "  .pcae/policy.toml" in output
    assert "  tasks/active/" in output


def test_import_bundle_without_dry_run_fails_clearly(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    bundle = tmp_path / "bundle.json"
    bundle.write_text("{}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["import", "bundle", "bundle.json"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Real import is not implemented yet. Use --dry-run." in output


def test_import_bundle_missing_file_fails_clearly(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["import", "bundle", "missing.json", "--dry-run"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Governance bundle not found: missing.json" in output


def test_import_bundle_invalid_json_fails_clearly(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    bundle = tmp_path / "bundle.json"
    bundle.write_text("{broken\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["import", "bundle", "bundle.json", "--dry-run"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Invalid governance bundle JSON:" in output


def test_import_bundle_missing_required_keys_fails_clearly(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    bundle = tmp_path / "bundle.json"
    bundle.write_text(json.dumps({"generated_timestamp": "now"}), encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["import", "bundle", "bundle.json", "--dry-run"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Invalid governance bundle: missing required keys:" in output
    assert "active_task" in output
    assert "session_snapshot" in output


def test_import_bundle_dry_run_is_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_ready_repo(tmp_path)
    commit_baseline(tmp_path)
    bundle = write_governance_export_bundle(
        HarnessPath(tmp_path),
        generated_at=datetime(2026, 5, 24, 9, 1, tzinfo=timezone.utc),
    )
    before = text_file_snapshot(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["import", "bundle", bundle.relative_path.as_posix(), "--dry-run"])

    after = text_file_snapshot(tmp_path)
    capsys.readouterr()
    assert exit_code == 0
    assert after == before


def init_ready_repo(root: Path) -> None:
    init_harness(HarnessPath(root))
    init_git_repo(root)
    create_task_contract(
        HarnessPath(root),
        "Import task",
        created_at=datetime(2026, 5, 24, 8, 0, tzinfo=timezone.utc),
    )


def init_git_repo(root: Path) -> None:
    run_git(root, "init")
    run_git(root, "config", "user.email", "test@example.com")
    run_git(root, "config", "user.name", "Test User")


def commit_baseline(root: Path) -> None:
    run_git(root, "add", ".")
    run_git(root, "commit", "-m", "baseline")


def run_git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )


def text_file_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(root).parts
    }
