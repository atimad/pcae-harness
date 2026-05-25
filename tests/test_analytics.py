from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.analytics import risk_level_for_score
from pcae.core.paths import HarnessPath
from pcae.core.session import write_session_snapshot
from pcae.core.tasks import create_task_contract


def test_analytics_trends_reports_human_summary(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_history(
        tmp_path,
        [
            history_entry("2026-05-23T08:00:00+00:00", 1, "advisory", "missing", {"core": 2}),
            history_entry("2026-05-23T08:01:00+00:00", 3, "strict", "verified", {"tests": 3}),
        ],
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["analytics", "trends"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Governance trends" in output
    assert "Total snapshots: 2" in output
    assert "First snapshot: 2026-05-23T08:00:00+00:00" in output
    assert "Latest snapshot: 2026-05-23T08:01:00+00:00" in output
    assert "Dependency warnings trend: increasing" in output
    assert "Max dependency warnings: 3" in output
    assert "Latest dependency warnings: 3" in output
    assert "Enforcement modes seen: advisory, strict" in output
    assert "Session continuity states seen: missing, verified" in output
    assert "Most frequently touched zone: tests" in output


def test_analytics_trends_json_reports_deterministic_summary(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_history(
        tmp_path,
        [
            history_entry("2026-05-23T08:00:00+00:00", 4, "strict", "verified", {"core": 3}),
            history_entry("2026-05-23T08:01:00+00:00", 2, "advisory", "missing", {"core": 1}),
        ],
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["analytics", "trends", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data == {
        "dependency_warnings_trend": "decreasing",
        "enforcement_modes_seen": ["advisory", "strict"],
        "first_snapshot_timestamp": "2026-05-23T08:00:00+00:00",
        "latest_dependency_warnings": 2,
        "latest_snapshot_timestamp": "2026-05-23T08:01:00+00:00",
        "max_dependency_warnings": 4,
        "most_frequently_touched_zone": "core",
        "session_continuity_states_seen": ["missing", "verified"],
        "total_snapshots": 2,
    }


def test_analytics_trends_reports_stable_dependency_warnings(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_history(
        tmp_path,
        [
            history_entry("2026-05-23T08:00:00+00:00", 2, "advisory", "verified", {}),
            history_entry("2026-05-23T08:01:00+00:00", 2, "advisory", "verified", {}),
        ],
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["analytics", "trends", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["dependency_warnings_trend"] == "stable"


def test_analytics_trends_empty_history_reports_insufficient_data(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_history(tmp_path, [])
    monkeypatch.chdir(tmp_path)

    exit_code = main(["analytics", "trends", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["total_snapshots"] == 0
    assert data["dependency_warnings_trend"] == "insufficient_data"
    assert data["first_snapshot_timestamp"] is None
    assert data["latest_snapshot_timestamp"] is None


def test_analytics_trends_missing_history_fails_clearly(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["analytics", "trends"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "No architecture history found at .pcae/architecture-history.json." in output


def test_analytics_trends_malformed_history_fails_clearly(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    target = tmp_path / ".pcae" / "architecture-history.json"
    target.parent.mkdir(parents=True)
    target.write_text("{bad json", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["analytics", "trends"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Invalid architecture history JSON:" in output


def test_analytics_risk_json_reports_low_risk_for_clean_repo(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_clean_governed_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["analytics", "risk", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["risk_score"] == 0
    assert data["risk_level"] == "low"
    assert data["contributing_factors"] == []
    assert data["dependency_warnings"] == 0
    assert data["session_continuity_state"] == "verified"
    assert data["policy_validation_state"] == "valid"
    assert data["git_cleanliness"] == "clean"
    assert data["fleet_drift_state"] == "none"


def test_analytics_risk_reports_medium_risk(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_clean_governed_repo(tmp_path, dependency_warnings=1)
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n\nDirty.\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["analytics", "risk"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Governance risk" in output
    assert "Risk score: 25" in output
    assert "Risk level: medium" in output
    assert "dependency warnings" in output
    assert "dirty git status" in output


def test_analytics_risk_json_reports_high_risk(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_clean_governed_repo(tmp_path)
    (tmp_path / ".pcae" / "policy.toml").write_text("bad", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["analytics", "risk", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["risk_score"] >= 60
    assert data["risk_level"] == "high"
    assert "invalid policy" in data["contributing_factors"]
    assert "check violations" in data["contributing_factors"]


def test_risk_level_thresholds() -> None:
    assert risk_level_for_score(0) == "low"
    assert risk_level_for_score(24) == "low"
    assert risk_level_for_score(25) == "medium"
    assert risk_level_for_score(59) == "medium"
    assert risk_level_for_score(60) == "high"
    assert risk_level_for_score(100) == "high"


def history_entry(
    timestamp: str,
    warnings: int,
    enforcement_mode: str,
    session_continuity: str,
    zones: dict[str, int],
) -> dict:
    return {
        "architecture_zones_touched": zones,
        "dependency_warnings_count": warnings,
        "enforcement_mode": enforcement_mode,
        "session_continuity": session_continuity,
        "timestamp": timestamp,
    }


def write_history(root: Path, entries: list[dict]) -> None:
    target = root / ".pcae" / "architecture-history.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(entries, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def init_clean_governed_repo(root: Path, dependency_warnings: int = 0) -> None:
    init_git_repo(root)
    init_harness(HarnessPath(root))
    task = create_task_contract(
        HarnessPath(root),
        "Analytics risk task",
        created_at=datetime(2026, 5, 25, 8, 0, tzinfo=timezone.utc),
    )
    task_path = root / task.relative_path
    task_path.write_text(
        task_path.read_text(encoding="utf-8").replace(
            "## Allowed Files\n\n- TBD",
            "## Allowed Files\n\n- *.md",
        ),
        encoding="utf-8",
    )
    write_session_snapshot(
        HarnessPath(root),
        created_at=datetime(2026, 5, 25, 8, 1, tzinfo=timezone.utc),
    )
    write_history(
        root,
        [
            history_entry(
                "2026-05-25T08:02:00+00:00",
                dependency_warnings,
                "advisory",
                "verified",
                {},
            )
        ],
    )
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
