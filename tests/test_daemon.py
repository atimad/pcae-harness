from __future__ import annotations

import json
from pathlib import Path

from pcae.cli import main


def test_daemon_run_without_dry_run_fails(capsys) -> None:
    exit_code = main(["daemon", "run"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Daemon run is only available with --dry-run in this phase." in output


def test_daemon_dry_run_human_output_works(capsys) -> None:
    exit_code = main(["daemon", "run", "--dry-run"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "PCAE daemon" in output
    assert "Mode: dry-run" in output
    assert "Monitoring cycles: 1" in output
    assert "1. pcae health: planned" in output
    assert "2. pcae check: planned" in output
    assert "3. pcae fleet drift: planned" in output
    assert "4. pcae analytics risk: planned" in output
    assert "5. pcae pipeline run --dry-run: planned" in output
    assert "Daemon result: planned" in output


def test_daemon_dry_run_json_output_works(capsys) -> None:
    exit_code = main(["daemon", "run", "--dry-run", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data == {
        "cycle_count": 1,
        "mode": "dry-run",
        "status": "planned",
        "steps": [
            {
                "name": "pcae health",
                "status": "planned",
                "summary": "would run during daemon monitoring cycle",
            },
            {
                "name": "pcae check",
                "status": "planned",
                "summary": "would run during daemon monitoring cycle",
            },
            {
                "name": "pcae fleet drift",
                "status": "planned",
                "summary": "would run during daemon monitoring cycle",
            },
            {
                "name": "pcae analytics risk",
                "status": "planned",
                "summary": "would run during daemon monitoring cycle",
            },
            {
                "name": "pcae pipeline run --dry-run",
                "status": "planned",
                "summary": "would run during daemon monitoring cycle",
            },
        ],
    }


def test_daemon_dry_run_writes_no_files(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    write_file(tmp_path / ".pcae" / "session.json", "{}\n")
    write_file(tmp_path / ".pcae" / "architecture-history.json", "[]\n")
    before = text_file_snapshot(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["daemon", "run", "--dry-run"])

    capsys.readouterr()
    after = text_file_snapshot(tmp_path)
    assert exit_code == 0
    assert after == before
    assert not (tmp_path / ".pcae" / "exports").exists()
    assert not (tmp_path / ".pcae" / "fleet-exports").exists()


def test_daemon_status_human_output_works(capsys) -> None:
    exit_code = main(["daemon", "status"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "PCAE daemon status" in output
    assert "Supported: true" in output
    assert "Running: false" in output
    assert "Mode: dry-run-only" in output
    assert "Watch supported: false" in output
    assert "Dry-run supported: true" in output
    assert "Planned checks: 5" in output
    assert "1. pcae health" in output
    assert "5. pcae pipeline run --dry-run" in output


def test_daemon_status_json_output_works(capsys) -> None:
    exit_code = main(["daemon", "status", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data == {
        "dry_run_supported": True,
        "mode": "dry-run-only",
        "planned_checks": [
            "pcae health",
            "pcae check",
            "pcae fleet drift",
            "pcae analytics risk",
            "pcae pipeline run --dry-run",
        ],
        "planned_checks_count": 5,
        "running": False,
        "supported": True,
        "watch_supported": False,
    }


def test_daemon_watch_requires_dry_run(capsys) -> None:
    exit_code = main(["daemon", "watch"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Daemon watch is only available with --dry-run in this phase." in output


def test_daemon_watch_dry_run_human_output_works(capsys) -> None:
    exit_code = main(["daemon", "watch", "--dry-run"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "PCAE daemon watch" in output
    assert "Mode: dry-run" in output
    assert "Interval seconds: 300" in output
    assert "Would repeat continuously: true" in output
    assert "Planned checks: 5" in output
    assert "1. pcae health" in output
    assert "5. pcae pipeline run --dry-run" in output


def test_daemon_watch_dry_run_custom_interval(capsys) -> None:
    exit_code = main(
        ["daemon", "watch", "--dry-run", "--interval-seconds", "60"]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Interval seconds: 60" in output


def test_daemon_watch_dry_run_json_output_works(capsys) -> None:
    exit_code = main(["daemon", "watch", "--dry-run", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data == {
        "interval_seconds": 300,
        "mode": "dry-run",
        "planned_checks": [
            "pcae health",
            "pcae check",
            "pcae fleet drift",
            "pcae analytics risk",
            "pcae pipeline run --dry-run",
        ],
        "planned_checks_count": 5,
        "would_repeat_continuously": True,
    }


def test_daemon_watch_invalid_interval_fails(capsys) -> None:
    exit_code = main(
        ["daemon", "watch", "--dry-run", "--interval-seconds", "0"]
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Interval seconds must be a positive integer." in output


def test_daemon_watch_dry_run_writes_no_files(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    write_file(tmp_path / ".pcae" / "session.json", "{}\n")
    write_file(tmp_path / ".pcae" / "architecture-history.json", "[]\n")
    before = text_file_snapshot(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["daemon", "watch", "--dry-run"])

    capsys.readouterr()
    after = text_file_snapshot(tmp_path)
    assert exit_code == 0
    assert after == before
    assert not (tmp_path / ".pcae" / "exports").exists()
    assert not (tmp_path / ".pcae" / "fleet-exports").exists()


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def text_file_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in root.rglob("*")
        if path.is_file()
    }
