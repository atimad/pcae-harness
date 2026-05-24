from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.architecture import analyze_changed_python_dependencies
from pcae.core.architecture import write_architecture_history_snapshot
from pcae.core.check import run_checks
from pcae.core.git_status import GitChange
from pcae.core.paths import HarnessPath


ZONES = {
    "core": ("src/pcae/core/**",),
    "commands": ("src/pcae/commands/**",),
    "tests": ("tests/**",),
}


def test_architecture_analysis_allows_configured_dependency(tmp_path: Path) -> None:
    write_file(tmp_path / "src" / "pcae" / "core" / "check.py", "import json\n")
    write_file(tmp_path / "src" / "pcae" / "core" / "tasks.py", "VALUE = 1\n")
    write_file(
        tmp_path / "src" / "pcae" / "core" / "changed.py",
        "import pcae.core.tasks\n",
    )

    result = analyze_changed_python_dependencies(
        HarnessPath(tmp_path),
        (GitChange(Path("src/pcae/core/changed.py"), " M"),),
        ZONES,
        {"core": ("core",)},
    )

    assert result.dependency_warnings == ()
    assert result.parse_warnings == ()


def test_architecture_analysis_reports_forbidden_dependency(tmp_path: Path) -> None:
    write_file(tmp_path / "src" / "pcae" / "commands" / "task.py", "VALUE = 1\n")
    write_file(
        tmp_path / "src" / "pcae" / "core" / "changed.py",
        "import pcae.commands.task\n",
    )

    result = analyze_changed_python_dependencies(
        HarnessPath(tmp_path),
        (GitChange(Path("src/pcae/core/changed.py"), " M"),),
        ZONES,
        {"core": ("core",), "commands": ("core", "commands")},
    )

    assert len(result.dependency_warnings) == 1
    assert result.dependency_warnings[0].text == (
        "src/pcae/core/changed.py: core -> commands is not allowed by policy"
    )
    assert result.parse_warnings == ()


def test_architecture_analysis_forbidden_dependency_wins_over_wildcard(
    tmp_path: Path,
) -> None:
    write_file(tmp_path / "src" / "pcae" / "commands" / "task.py", "VALUE = 1\n")
    write_file(
        tmp_path / "src" / "pcae" / "core" / "changed.py",
        "import pcae.commands.task\n",
    )

    result = analyze_changed_python_dependencies(
        HarnessPath(tmp_path),
        (GitChange(Path("src/pcae/core/changed.py"), " M"),),
        ZONES,
        {"core": ("*",)},
        (("core", "commands"),),
    )

    assert len(result.dependency_warnings) == 1
    assert result.dependency_warnings[0].text == (
        "src/pcae/core/changed.py: core -> commands is not allowed by policy"
    )


def test_architecture_analysis_ignores_external_imports(tmp_path: Path) -> None:
    write_file(
        tmp_path / "src" / "pcae" / "core" / "changed.py",
        "import argparse\nfrom pathlib import Path\n",
    )

    result = analyze_changed_python_dependencies(
        HarnessPath(tmp_path),
        (GitChange(Path("src/pcae/core/changed.py"), " M"),),
        ZONES,
        {"core": ("core",)},
    )

    assert result.dependency_warnings == ()
    assert result.parse_warnings == ()


def test_architecture_analysis_warns_on_parse_error(tmp_path: Path) -> None:
    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "def broken(:\n")

    result = analyze_changed_python_dependencies(
        HarnessPath(tmp_path),
        (GitChange(Path("src/pcae/core/changed.py"), " M"),),
        ZONES,
        {"core": ("core",)},
    )

    assert result.dependency_warnings == ()
    assert len(result.parse_warnings) == 1
    assert result.parse_warnings[0].path == Path("src/pcae/core/changed.py")
    assert "Could not parse Python imports:" in result.parse_warnings[0].text


def test_architecture_analysis_skips_when_rules_are_missing(tmp_path: Path) -> None:
    write_file(tmp_path / "src" / "pcae" / "commands" / "task.py", "VALUE = 1\n")
    write_file(
        tmp_path / "src" / "pcae" / "core" / "changed.py",
        "import pcae.commands.task\n",
    )

    result = analyze_changed_python_dependencies(
        HarnessPath(tmp_path),
        (GitChange(Path("src/pcae/core/changed.py"), " M"),),
        ZONES,
        {},
    )

    assert result.dependency_warnings == ()
    assert result.parse_warnings == ()


def test_architecture_analysis_skips_unclassified_source(tmp_path: Path) -> None:
    write_file(tmp_path / "src" / "pcae" / "commands" / "task.py", "VALUE = 1\n")
    write_file(tmp_path / "scratch.py", "import pcae.commands.task\n")

    result = analyze_changed_python_dependencies(
        HarnessPath(tmp_path),
        (GitChange(Path("scratch.py"), " M"),),
        ZONES,
        {"core": ("core",), "commands": ("core", "commands")},
    )

    assert result.dependency_warnings == ()
    assert result.parse_warnings == ()


def test_architecture_snapshot_creates_history_file(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path)
    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "print('old')\n")
    commit_baseline(tmp_path)

    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "print('new')\n")
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")
    result = run_checks(HarnessPath(tmp_path))

    snapshot = write_architecture_history_snapshot(
        HarnessPath(tmp_path),
        result,
        created_at=datetime(2026, 5, 23, 8, 0, tzinfo=timezone.utc),
    )

    history_file = tmp_path / ".pcae" / "architecture-history.json"
    data = json.loads(history_file.read_text(encoding="utf-8"))
    assert snapshot.relative_path == Path(".pcae/architecture-history.json")
    assert len(data) == 1
    assert data[0]["timestamp"] == "2026-05-23T08:00:00+00:00"
    assert data[0]["active_task"] == {
        "id": "20260522-1930-test-task",
        "title": "Test task",
    }
    assert data[0]["architecture_zones_touched"] == {
        "core": 1,
        "docs": 1,
    }
    assert data[0]["changed_files_count"] == 2
    assert data[0]["dependency_warnings_count"] == 0
    assert data[0]["enforcement_mode"] == "advisory"
    assert data[0]["git_branch"] in {"main", "master"}
    assert data[0]["session_continuity"] == "missing"


def test_architecture_snapshot_appends_history_entries(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path)
    commit_baseline(tmp_path)
    result = run_checks(HarnessPath(tmp_path))

    write_architecture_history_snapshot(
        HarnessPath(tmp_path),
        result,
        created_at=datetime(2026, 5, 23, 8, 0, tzinfo=timezone.utc),
    )
    write_architecture_history_snapshot(
        HarnessPath(tmp_path),
        result,
        created_at=datetime(2026, 5, 23, 8, 1, tzinfo=timezone.utc),
    )

    data = json.loads(
        (tmp_path / ".pcae" / "architecture-history.json").read_text(
            encoding="utf-8"
        )
    )
    assert [entry["timestamp"] for entry in data] == [
        "2026-05-23T08:00:00+00:00",
        "2026-05-23T08:01:00+00:00",
    ]


def test_architecture_snapshot_command_writes_history(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["architecture", "snapshot"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Wrote architecture history: .pcae/architecture-history.json" in output
    assert "Entries: 1" in output
    assert "Snapshot metrics:" in output
    assert "  Total snapshots: 1" in output
    assert "  Latest dependency warnings: 0" in output
    assert "  Max dependency warnings: 0" in output
    assert "  Snapshots with warnings: 0" in output
    assert "  Most frequently touched zone: none" in output
    assert (tmp_path / ".pcae" / "architecture-history.json").is_file()


def test_architecture_history_command_prints_latest_summary(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path)
    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "print('old')\n")
    commit_baseline(tmp_path)

    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "print('new')\n")
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")
    result = run_checks(HarnessPath(tmp_path))
    write_architecture_history_snapshot(
        HarnessPath(tmp_path),
        result,
        created_at=datetime(2026, 5, 23, 8, 0, tzinfo=timezone.utc),
    )
    write_architecture_history_snapshot(
        HarnessPath(tmp_path),
        result,
        created_at=datetime(2026, 5, 23, 8, 1, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["architecture", "history"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Architecture history: .pcae/architecture-history.json" in output
    assert "Total entries: 2" in output
    assert "Latest snapshot: 2026-05-23T08:01:00+00:00" in output
    assert "Latest active task: 20260522-1930-test-task" in output
    assert "Latest active task title: Test task" in output
    assert "Latest enforcement mode: advisory" in output
    assert "Latest session continuity: missing" in output
    assert "Latest dependency warnings: 0" in output
    assert "Latest architecture zones touched:" in output
    assert "  core: 1 files" in output
    assert "  docs: 1 files" in output


def test_architecture_history_command_reports_missing_history(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["architecture", "history"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "No architecture history found at .pcae/architecture-history.json." in output


def test_architecture_history_command_reports_malformed_history(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    history_file = tmp_path / ".pcae" / "architecture-history.json"
    history_file.parent.mkdir(parents=True, exist_ok=True)
    history_file.write_text("{broken\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["architecture", "history"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Invalid architecture history JSON:" in output


def test_architecture_metrics_command_prints_drift_metrics(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_history(
        tmp_path,
        [
            {
                "architecture_zones_touched": {"core": 2, "docs": 1},
                "dependency_warnings_count": 0,
                "enforcement_mode": "advisory",
                "session_continuity": "missing",
                "timestamp": "2026-05-23T08:00:00+00:00",
            },
            {
                "architecture_zones_touched": {"core": 1, "tests": 4},
                "dependency_warnings_count": 3,
                "enforcement_mode": "strict",
                "session_continuity": "verified",
                "timestamp": "2026-05-23T08:01:00+00:00",
            },
            {
                "architecture_zones_touched": {"docs": 2},
                "dependency_warnings_count": 1,
                "enforcement_mode": "advisory",
                "session_continuity": "verified",
                "timestamp": "2026-05-23T08:02:00+00:00",
            },
        ],
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["architecture", "metrics"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Architecture drift metrics" in output
    assert "Total snapshots: 3" in output
    assert "Latest dependency warnings: 1" in output
    assert "Max dependency warnings: 3" in output
    assert "Average dependency warnings: 1.33" in output
    assert "Snapshots with warnings: 2" in output
    assert "Most frequently touched zone: tests" in output
    assert "Latest enforcement mode: advisory" in output
    assert "Latest session continuity: verified" in output


def test_architecture_metrics_json_command_prints_drift_metrics(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_history(
        tmp_path,
        [
            {
                "architecture_zones_touched": {"core": 2, "docs": 1},
                "dependency_warnings_count": 0,
                "enforcement_mode": "advisory",
                "session_continuity": "missing",
            },
            {
                "architecture_zones_touched": {"core": 1, "tests": 4},
                "dependency_warnings_count": 3,
                "enforcement_mode": "strict",
                "session_continuity": "verified",
            },
            {
                "architecture_zones_touched": {"docs": 2},
                "dependency_warnings_count": 1,
                "enforcement_mode": "advisory",
                "session_continuity": "verified",
            },
        ],
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["architecture", "metrics", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data == {
        "average_dependency_warnings": 4 / 3,
        "latest_dependency_warnings": 1,
        "latest_enforcement_mode": "advisory",
        "latest_session_continuity": "verified",
        "max_dependency_warnings": 3,
        "most_frequently_touched_zone": "tests",
        "snapshots_with_warnings": 2,
        "total_snapshots": 3,
    }


def test_architecture_metrics_command_reports_missing_history(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["architecture", "metrics"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "No architecture history found at .pcae/architecture-history.json." in output


def test_architecture_metrics_command_reports_malformed_history(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    history_file = tmp_path / ".pcae" / "architecture-history.json"
    history_file.parent.mkdir(parents=True, exist_ok=True)
    history_file.write_text("{broken\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["architecture", "metrics"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Invalid architecture history JSON:" in output


def test_architecture_metrics_command_reports_empty_history(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_history(tmp_path, [])
    monkeypatch.chdir(tmp_path)

    exit_code = main(["architecture", "metrics"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Invalid architecture history: no entries found." in output


def write_task(root: Path) -> None:
    task_path = root / "tasks" / "active" / "20260522-1930-test-task.md"
    write_file(
        task_path,
        """# Task Contract

## Task ID

20260522-1930-test-task

## Title

Test task

## Allowed Files

- src/pcae/core/changed.py
- CHANGELOG.md
""",
    )


def commit_baseline(root: Path) -> None:
    run_git(root, "init")
    run_git(root, "config", "user.email", "test@example.com")
    run_git(root, "config", "user.name", "Test User")
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


def write_history(root: Path, entries: list[dict]) -> None:
    history_file = root / ".pcae" / "architecture-history.json"
    history_file.parent.mkdir(parents=True, exist_ok=True)
    history_file.write_text(json.dumps(entries), encoding="utf-8")
