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


EXPECTED_BUNDLE_KEYS = {
    "active_task",
    "architecture_metrics",
    "check_summary",
    "generated_timestamp",
    "git_status_summary",
    "health_summary",
    "latest_architecture_history_summary",
    "policy_summary",
    "session_snapshot",
}


def test_export_bundle_command_writes_governance_bundle(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_ready_repo(tmp_path)
    write_session_snapshot(
        HarnessPath(tmp_path),
        created_at=datetime(2026, 5, 24, 8, 0, tzinfo=timezone.utc),
    )
    write_architecture_history(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["export", "bundle"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Wrote governance bundle: .pcae/exports/governance-bundle-" in output

    bundle_paths = sorted((tmp_path / ".pcae" / "exports").glob("*.json"))
    assert len(bundle_paths) == 1
    data = json.loads(bundle_paths[0].read_text(encoding="utf-8"))
    assert set(data) == EXPECTED_BUNDLE_KEYS
    assert data["active_task"] == {
        "id": "20260524-0800-export-task",
        "title": "Export task",
    }
    assert data["session_snapshot"]["active_task"]["id"] == (
        "20260524-0800-export-task"
    )
    assert data["health_summary"]["overall_status"] == "healthy"
    assert data["check_summary"]["status"] == "passed"
    assert data["architecture_metrics"]["total_snapshots"] == 1
    assert data["latest_architecture_history_summary"]["entries"] == 1
    assert data["policy_summary"]["valid"] is True
    assert data["git_status_summary"]["summary"] == "clean"


def test_export_bundle_uses_deterministic_timestamped_filename(
    tmp_path: Path,
) -> None:
    init_ready_repo(tmp_path)
    commit_baseline(tmp_path)

    bundle = write_governance_export_bundle(
        HarnessPath(tmp_path),
        generated_at=datetime(2026, 5, 24, 9, 30, 5, tzinfo=timezone.utc),
    )

    assert bundle.relative_path.as_posix() == (
        ".pcae/exports/governance-bundle-20260524-093005.json"
    )
    assert bundle.data["generated_timestamp"] == "2026-05-24T09:30:05+00:00"
    assert (tmp_path / bundle.relative_path).is_file()


def test_export_bundle_handles_missing_session_and_history(
    tmp_path: Path,
) -> None:
    init_ready_repo(tmp_path)
    commit_baseline(tmp_path)

    bundle = write_governance_export_bundle(
        HarnessPath(tmp_path),
        generated_at=datetime(2026, 5, 24, 9, 31, tzinfo=timezone.utc),
    )

    assert bundle.data["session_snapshot"] is None
    assert bundle.data["architecture_metrics"] is None
    assert bundle.data["latest_architecture_history_summary"] is None
    assert bundle.data["check_summary"]["session_continuity"] == "missing"
    assert bundle.data["health_summary"]["overall_status"] == "healthy"


def init_ready_repo(root: Path) -> None:
    init_harness(HarnessPath(root))
    init_git_repo(root)
    create_task_contract(
        HarnessPath(root),
        "Export task",
        created_at=datetime(2026, 5, 24, 8, 0, tzinfo=timezone.utc),
    )


def write_architecture_history(root: Path) -> None:
    write_file(
        root / ".pcae" / "architecture-history.json",
        json.dumps(
            [
                {
                    "active_task": {
                        "id": "20260524-0800-export-task",
                        "title": "Export task",
                    },
                    "architecture_zones_touched": {},
                    "changed_files_count": 0,
                    "dependency_warnings_count": 0,
                    "enforcement_mode": "advisory",
                    "git_branch": "main",
                    "session_continuity": "verified",
                    "timestamp": "2026-05-24T08:00:00+00:00",
                }
            ]
        ),
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


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
