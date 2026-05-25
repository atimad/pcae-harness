from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.paths import HarnessPath
from pcae.core.session import write_session_snapshot
from pcae.core.tasks import create_task_contract


def test_pipeline_run_default_works(tmp_path: Path, monkeypatch, capsys) -> None:
    init_pipeline_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["pipeline", "run"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Pipeline: default" in output
    assert "- pcae health: passed" in output
    assert "- pcae check: passed" in output
    assert "- pcae analytics risk: passed" in output
    assert "- pcae analytics trends: passed" in output
    assert "- pcae architecture metrics: passed" in output
    assert "- pcae export bundle: passed" in output
    assert "- pcae fleet export: passed" in output
    assert "- pcae session end: passed" in output
    assert "Pipeline result: passed" in output
    assert list((tmp_path / ".pcae" / "exports").glob("governance-bundle-*.json"))
    assert list(
        (tmp_path / ".pcae" / "fleet-exports").glob(
            "fleet-governance-bundle-*.json"
        )
    )


def test_pipeline_run_default_name_works(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_pipeline_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["pipeline", "run", "default"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Pipeline: default" in output
    assert "Pipeline result: passed" in output


def test_pipeline_run_json_works(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_pipeline_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["pipeline", "run", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["pipeline_name"] == "default"
    assert data["overall_status"] == "passed"
    assert data["stopped_at"] is None
    assert "generated_timestamp" in data
    assert [step["name"] for step in data["steps"]] == [
        "pcae health",
        "pcae check",
        "pcae analytics risk",
        "pcae analytics trends",
        "pcae architecture metrics",
        "pcae export bundle",
        "pcae fleet export",
        "pcae session end",
    ]
    export_step = data["steps"][5]
    fleet_step = data["steps"][6]
    session_step = data["steps"][7]
    assert export_step["artifacts"][0].startswith(
        ".pcae/exports/governance-bundle-"
    )
    assert fleet_step["artifacts"][0].startswith(
        ".pcae/fleet-exports/fleet-governance-bundle-"
    )
    assert session_step["artifacts"] == [
        ".pcae/session.json",
        ".pcae/architecture-history.json",
    ]


def test_pipeline_run_default_json_works(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_pipeline_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["pipeline", "run", "default", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["pipeline_name"] == "default"
    assert data["overall_status"] == "passed"


def test_pipeline_stops_on_failed_health(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["pipeline", "run"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "- pcae health: failed" in output
    assert "pcae check" not in output
    assert not (tmp_path / ".pcae" / "exports").exists()


def test_pipeline_stop_json_reports_stopped_at(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["pipeline", "run", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["overall_status"] == "failed"
    assert data["stopped_at"] == "pcae health"
    assert data["steps"] == [
        {
            "artifacts": [],
            "name": "pcae health",
            "status": "failed",
            "summary": "governance health is unhealthy",
        }
    ]


def test_pipeline_stops_on_failed_check(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_pipeline_repo(tmp_path)
    monkeypatch.setattr(
        "pcae.core.pipeline.build_health_data",
        lambda root: {"overall_status": "healthy"},
    )
    monkeypatch.setattr(
        "pcae.core.pipeline.run_checks",
        lambda root: SimpleNamespace(passed=False, violations=()),
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["pipeline", "run"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "- pcae health: passed" in output
    assert "- pcae check: failed" in output
    assert "pcae export bundle" not in output


def test_pipeline_export_artifacts_remain_ignored(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_pipeline_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["pipeline", "run"])
    capsys.readouterr()

    status = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert exit_code == 0
    assert "governance-bundle-" not in status
    assert "fleet-governance-bundle-" not in status


def init_pipeline_repo(root: Path) -> None:
    init_git_repo(root)
    init_harness(HarnessPath(root))
    write_fleet_export_ignore(root)
    task = create_task_contract(
        HarnessPath(root),
        "Pipeline task",
        created_at=datetime(2026, 5, 25, 8, 0, tzinfo=timezone.utc),
    )
    task_path = root / task.relative_path
    task_path.write_text(
        task_path.read_text(encoding="utf-8").replace(
            "## Allowed Files\n\n- TBD",
            "## Allowed Files\n\n- src/**\n- tests/**\n- *.md\n- .pcae/**",
        ),
        encoding="utf-8",
    )
    write_session_snapshot(
        HarnessPath(root),
        created_at=datetime(2026, 5, 25, 8, 1, tzinfo=timezone.utc),
    )
    write_history(root)
    subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "baseline"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )


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


def write_history(root: Path) -> None:
    target = root / ".pcae" / "architecture-history.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(
            [
                {
                    "architecture_zones_touched": {},
                    "dependency_warnings_count": 0,
                    "enforcement_mode": "advisory",
                    "session_continuity": "verified",
                    "timestamp": "2026-05-25T08:02:00+00:00",
                }
            ],
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def write_fleet_export_ignore(root: Path) -> None:
    target = root / ".pcae" / "fleet-exports" / ".gitignore"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("fleet-governance-bundle-*.json\n", encoding="utf-8")
