from __future__ import annotations

import json
from pathlib import Path

from pcae.cli import main


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
    target.parent.mkdir(parents=True)
    target.write_text(
        json.dumps(entries, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
