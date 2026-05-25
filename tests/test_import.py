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
    assert "Architecture history restore mode: replace" in output
    assert "  .pcae/session.json" in output
    assert "  .pcae/architecture-history.json" in output
    assert "  .pcae/policy.toml" in output
    assert "  tasks/active/" in output


def test_import_bundle_without_dry_run_restores_session(
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
        generated_at=datetime(2026, 5, 24, 9, 2, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)

    (tmp_path / ".pcae" / "session.json").unlink()

    exit_code = main(["import", "bundle", bundle.relative_path.as_posix()])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Restored governance bundle." in output
    assert "  wrote .pcae/session.json" in output
    assert (tmp_path / ".pcae" / "session.json").is_file()


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


def test_import_bundle_dry_run_merge_history_reports_merge_without_writing(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_ready_repo(tmp_path)
    write_history(tmp_path)
    commit_baseline(tmp_path)
    bundle = write_governance_export_bundle(
        HarnessPath(tmp_path),
        generated_at=datetime(2026, 5, 24, 9, 5, tzinfo=timezone.utc),
    )
    before = text_file_snapshot(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        [
            "import",
            "bundle",
            bundle.relative_path.as_posix(),
            "--dry-run",
            "--merge-history",
        ]
    )

    after = text_file_snapshot(tmp_path)
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Architecture history restore mode: merge" in output
    assert after == before


def test_import_bundle_restores_session_and_history(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_ready_repo(tmp_path)
    write_session_snapshot(
        HarnessPath(tmp_path),
        created_at=datetime(2026, 5, 24, 8, 0, tzinfo=timezone.utc),
    )
    write_history(tmp_path)
    commit_baseline(tmp_path)
    bundle = write_governance_export_bundle(
        HarnessPath(tmp_path),
        generated_at=datetime(2026, 5, 24, 9, 3, tzinfo=timezone.utc),
    )
    (tmp_path / ".pcae" / "session.json").unlink()
    (tmp_path / ".pcae" / "architecture-history.json").unlink()
    policy_before = (tmp_path / ".pcae" / "policy.toml").read_text(encoding="utf-8")
    task_before = next((tmp_path / "tasks" / "active").glob("*.md")).read_text(
        encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["import", "bundle", bundle.relative_path.as_posix()])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "  wrote .pcae/session.json" in output
    assert "  wrote .pcae/architecture-history.json" in output
    session_data = json.loads((tmp_path / ".pcae" / "session.json").read_text())
    history_data = json.loads(
        (tmp_path / ".pcae" / "architecture-history.json").read_text()
    )
    assert session_data["active_task"]["id"] == "20260524-0800-import-task"
    assert history_data[0]["active_task"]["id"] == "20260524-0800-import-task"
    assert (tmp_path / ".pcae" / "policy.toml").read_text(
        encoding="utf-8"
    ) == policy_before
    assert next((tmp_path / "tasks" / "active").glob("*.md")).read_text(
        encoding="utf-8"
    ) == task_before


def test_import_bundle_merge_history_combines_deduplicates_and_sorts(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_ready_repo(tmp_path)
    write_session_snapshot(
        HarnessPath(tmp_path),
        created_at=datetime(2026, 5, 24, 8, 0, tzinfo=timezone.utc),
    )
    write_history_entries(
        tmp_path,
        [
            history_entry("2026-05-24T08:00:00+00:00", "local-old"),
            history_entry("2026-05-24T08:20:00+00:00", "duplicate-local"),
        ],
    )
    commit_baseline(tmp_path)
    bundle = write_governance_export_bundle(
        HarnessPath(tmp_path),
        generated_at=datetime(2026, 5, 24, 9, 6, tzinfo=timezone.utc),
    )
    bundle_path = tmp_path / bundle.relative_path
    data = json.loads(bundle_path.read_text(encoding="utf-8"))
    data["latest_architecture_history_summary"]["entries_data"] = [
        history_entry("2026-05-24T08:10:00+00:00", "imported-middle"),
        history_entry("2026-05-24T08:20:00+00:00", "duplicate-imported"),
        history_entry("2026-05-24T08:30:00+00:00", "imported-new"),
    ]
    bundle_path.write_text(json.dumps(data), encoding="utf-8")
    write_history_entries(
        tmp_path,
        [
            history_entry("2026-05-24T08:00:00+00:00", "local-old"),
            history_entry("2026-05-24T08:20:00+00:00", "duplicate-local"),
        ],
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["import", "bundle", bundle.relative_path.as_posix(), "--merge-history"]
    )

    output = capsys.readouterr().out
    history = json.loads(
        (tmp_path / ".pcae" / "architecture-history.json").read_text()
    )
    assert exit_code == 0
    assert "  wrote .pcae/architecture-history.json" in output
    assert [entry["timestamp"] for entry in history] == [
        "2026-05-24T08:00:00+00:00",
        "2026-05-24T08:10:00+00:00",
        "2026-05-24T08:20:00+00:00",
        "2026-05-24T08:30:00+00:00",
    ]
    assert [entry["label"] for entry in history] == [
        "local-old",
        "imported-middle",
        "duplicate-local",
        "imported-new",
    ]


def test_import_bundle_refuses_unhealthy_bundle(
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
        generated_at=datetime(2026, 5, 24, 9, 4, tzinfo=timezone.utc),
    )
    bundle_path = tmp_path / bundle.relative_path
    data = json.loads(bundle_path.read_text(encoding="utf-8"))
    data["health_summary"]["overall_status"] = "unhealthy"
    bundle_path.write_text(json.dumps(data), encoding="utf-8")
    before = text_file_snapshot(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["import", "bundle", bundle.relative_path.as_posix()])

    after = text_file_snapshot(tmp_path)
    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Refusing to restore governance bundle" in output
    assert after == before


def init_ready_repo(root: Path) -> None:
    init_harness(HarnessPath(root))
    init_git_repo(root)
    create_task_contract(
        HarnessPath(root),
        "Import task",
        created_at=datetime(2026, 5, 24, 8, 0, tzinfo=timezone.utc),
    )


def write_history(root: Path) -> None:
    history = [history_entry("2026-05-24T08:00:00+00:00", "baseline")]
    write_history_entries(root, history)


def write_history_entries(root: Path, entries: list[dict]) -> None:
    path = root / ".pcae" / "architecture-history.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries), encoding="utf-8")


def history_entry(timestamp: str, label: str) -> dict:
    return {
        "active_task": {
            "id": "20260524-0800-import-task",
            "title": "Import task",
        },
        "architecture_zones_touched": {},
        "changed_files_count": 0,
        "dependency_warnings_count": 0,
        "enforcement_mode": "advisory",
        "git_branch": "main",
        "label": label,
        "session_continuity": "verified",
        "timestamp": timestamp,
    }


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
