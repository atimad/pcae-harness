from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.architecture import (
    ADR_HUMAN_APPROVED_STATUS,
    ADR_INSPECTION_ADVISORY,
    ADR_VALID_STATUSES,
    ArchitectureDecisionRecord,
    analyze_changed_python_dependencies,
    create_adr,
    get_adr_registry,
    list_architecture_decisions,
    lookup_adr_by_id,
    write_architecture_history_snapshot,
)
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


# ---------------------------------------------------------------------------
# Architecture Decision Record model tests (Phase 36F)
# ---------------------------------------------------------------------------

def test_adr_valid_statuses_contains_all_required() -> None:
    assert "proposed" in ADR_VALID_STATUSES
    assert "accepted" in ADR_VALID_STATUSES
    assert "superseded" in ADR_VALID_STATUSES
    assert "deprecated" in ADR_VALID_STATUSES
    assert len(ADR_VALID_STATUSES) == 4


def test_adr_human_approved_status_is_accepted() -> None:
    assert ADR_HUMAN_APPROVED_STATUS == "accepted"


def test_create_adr_minimal_required_fields() -> None:
    adr = create_adr(
        decision_id="ADR-001",
        title="Use TOML for policy configuration",
        status="proposed",
        rationale="TOML is human-readable and widely supported.",
        author="alice",
    )
    assert adr.decision_id == "ADR-001"
    assert adr.title == "Use TOML for policy configuration"
    assert adr.status == "proposed"
    assert adr.rationale == "TOML is human-readable and widely supported."
    assert adr.author == "alice"
    assert adr.alternatives_considered == ()
    assert adr.consequences == ()
    assert adr.phase_reference is None
    assert adr.contributors == ()


def test_create_adr_all_fields() -> None:
    fixed_time = datetime(2026, 5, 29, 12, 0, tzinfo=timezone.utc)
    adr = create_adr(
        decision_id="ADR-002",
        title="Adopt Architecture Memory as next roadmap option",
        status="accepted",
        rationale="Architecture Memory provides governed ADR lifecycle.",
        alternatives_considered=["Option C — Multi-Agent", "Remote Coding"],
        consequences=["ADR model is now a first-class PCAE artifact."],
        created_at=fixed_time,
        phase_reference="36F",
        author="alice",
        contributors=["claude-local", "codex-local"],
    )
    assert adr.decision_id == "ADR-002"
    assert adr.status == "accepted"
    assert adr.alternatives_considered == ("Option C — Multi-Agent", "Remote Coding")
    assert adr.consequences == ("ADR model is now a first-class PCAE artifact.",)
    assert adr.created_at == fixed_time
    assert adr.phase_reference == "36F"
    assert adr.contributors == ("claude-local", "codex-local")


def test_create_adr_all_valid_statuses() -> None:
    for status in ("proposed", "accepted", "superseded", "deprecated"):
        adr = create_adr(
            decision_id=f"ADR-{status}",
            title=f"Decision with status {status}",
            status=status,
            rationale="Rationale.",
            author="alice",
        )
        assert adr.status == status


def test_create_adr_invalid_status_raises_value_error() -> None:
    import pytest
    with pytest.raises(ValueError, match="Invalid ADR status"):
        create_adr(
            decision_id="ADR-bad",
            title="Bad status",
            status="approved",
            rationale="Rationale.",
            author="alice",
        )


def test_create_adr_invalid_status_error_lists_valid_statuses() -> None:
    import pytest
    with pytest.raises(ValueError) as exc_info:
        create_adr(
            decision_id="ADR-bad",
            title="Bad status",
            status="unknown",
            rationale="Rationale.",
            author="alice",
        )
    message = str(exc_info.value)
    assert "accepted" in message
    assert "proposed" in message
    assert "superseded" in message
    assert "deprecated" in message


def test_create_adr_empty_author_raises_value_error() -> None:
    import pytest
    with pytest.raises(ValueError, match="author must be a non-empty string"):
        create_adr(
            decision_id="ADR-003",
            title="Missing author",
            status="proposed",
            rationale="Rationale.",
            author="",
        )


def test_create_adr_empty_decision_id_raises_value_error() -> None:
    import pytest
    with pytest.raises(ValueError, match="decision_id must be a non-empty string"):
        create_adr(
            decision_id="",
            title="No ID",
            status="proposed",
            rationale="Rationale.",
            author="alice",
        )


def test_create_adr_empty_title_raises_value_error() -> None:
    import pytest
    with pytest.raises(ValueError, match="title must be a non-empty string"):
        create_adr(
            decision_id="ADR-004",
            title="",
            status="proposed",
            rationale="Rationale.",
            author="alice",
        )


def test_create_adr_empty_rationale_raises_value_error() -> None:
    import pytest
    with pytest.raises(ValueError, match="rationale must be a non-empty string"):
        create_adr(
            decision_id="ADR-005",
            title="No rationale",
            status="proposed",
            rationale="",
            author="alice",
        )


def test_adr_is_human_approved_true_for_accepted() -> None:
    adr = create_adr(
        decision_id="ADR-006",
        title="Accepted decision",
        status="accepted",
        rationale="Rationale.",
        author="alice",
    )
    assert adr.is_human_approved is True


def test_adr_is_human_approved_false_for_non_accepted_statuses() -> None:
    for status in ("proposed", "superseded", "deprecated"):
        adr = create_adr(
            decision_id=f"ADR-{status}",
            title=f"Decision with status {status}",
            status=status,
            rationale="Rationale.",
            author="alice",
        )
        assert adr.is_human_approved is False, f"Expected False for status={status}"


def test_adr_to_dict_shape_and_values() -> None:
    fixed_time = datetime(2026, 5, 29, 12, 0, tzinfo=timezone.utc)
    adr = create_adr(
        decision_id="ADR-007",
        title="Dict shape test",
        status="proposed",
        rationale="Rationale.",
        author="alice",
        alternatives_considered=["Option A"],
        consequences=["Consequence B"],
        created_at=fixed_time,
        phase_reference="36F",
        contributors=["claude-local"],
    )
    d = adr.to_dict()
    assert set(d) == {
        "decision_id",
        "title",
        "status",
        "rationale",
        "alternatives_considered",
        "consequences",
        "created_at",
        "phase_reference",
        "author",
        "contributors",
        "is_human_approved",
    }
    assert d["decision_id"] == "ADR-007"
    assert d["status"] == "proposed"
    assert d["author"] == "alice"
    assert d["alternatives_considered"] == ["Option A"]
    assert d["consequences"] == ["Consequence B"]
    assert d["created_at"] == "2026-05-29T12:00:00+00:00"
    assert d["phase_reference"] == "36F"
    assert d["contributors"] == ["claude-local"]
    assert d["is_human_approved"] is False


def test_adr_contributors_vendor_neutral_accepts_any_string_ids() -> None:
    adr = create_adr(
        decision_id="ADR-008",
        title="Vendor-neutral contributors",
        status="accepted",
        rationale="Any agent identifier is valid.",
        author="alice",
        contributors=[
            "claude-local",
            "codex-local",
            "kimi-remote",
            "deepseek-api",
            "human-reviewer",
        ],
    )
    assert len(adr.contributors) == 5
    assert "claude-local" in adr.contributors
    assert "deepseek-api" in adr.contributors


def test_adr_is_frozen_dataclass() -> None:
    import pytest
    adr = create_adr(
        decision_id="ADR-009",
        title="Immutable",
        status="proposed",
        rationale="Rationale.",
        author="alice",
    )
    with pytest.raises((AttributeError, TypeError)):
        adr.status = "accepted"  # type: ignore[misc]


def test_create_adr_created_at_defaults_to_utc_now() -> None:
    before = datetime.now(timezone.utc)
    adr = create_adr(
        decision_id="ADR-010",
        title="Auto timestamp",
        status="proposed",
        rationale="Rationale.",
        author="alice",
    )
    after = datetime.now(timezone.utc)
    assert before <= adr.created_at <= after


# ---------------------------------------------------------------------------
# ADR inspection API tests (Phase 36G)
# ---------------------------------------------------------------------------

def _make_sample_registry() -> tuple[ArchitectureDecisionRecord, ...]:
    return (
        create_adr(
            decision_id="ADR-T001",
            title="First test decision",
            status="accepted",
            rationale="Test rationale A.",
            alternatives_considered=["Option X"],
            consequences=["Consequence Y"],
            created_at=datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
            phase_reference="36G",
            author="alice",
            contributors=["claude-local"],
        ),
        create_adr(
            decision_id="ADR-T002",
            title="Second test decision",
            status="proposed",
            rationale="Test rationale B.",
            created_at=datetime(2026, 2, 1, 0, 0, tzinfo=timezone.utc),
            phase_reference=None,
            author="bob",
        ),
    )


def test_list_architecture_decisions_empty_registry() -> None:
    result = list_architecture_decisions(())
    assert result.decisions == ()
    assert result.advisory == ADR_INSPECTION_ADVISORY


def test_list_architecture_decisions_populated_registry() -> None:
    registry = _make_sample_registry()
    result = list_architecture_decisions(registry)
    assert len(result.decisions) == 2
    assert result.decisions[0].decision_id == "ADR-T001"
    assert result.decisions[1].decision_id == "ADR-T002"
    assert result.advisory == ADR_INSPECTION_ADVISORY


def test_list_architecture_decisions_to_dict_shape() -> None:
    registry = _make_sample_registry()
    d = list_architecture_decisions(registry).to_dict()
    assert d["decision_count"] == 2
    assert len(d["decisions"]) == 2
    assert d["advisory"] == ADR_INSPECTION_ADVISORY
    first = d["decisions"][0]
    assert first["decision_id"] == "ADR-T001"
    assert first["title"] == "First test decision"
    assert first["status"] == "accepted"
    assert first["is_human_approved"] is True


def test_lookup_adr_by_id_found() -> None:
    registry = _make_sample_registry()
    adr = lookup_adr_by_id("ADR-T001", registry)
    assert adr is not None
    assert adr.decision_id == "ADR-T001"
    assert adr.title == "First test decision"


def test_lookup_adr_by_id_not_found_returns_none() -> None:
    registry = _make_sample_registry()
    result = lookup_adr_by_id("ADR-MISSING", registry)
    assert result is None


def test_lookup_adr_by_id_empty_registry() -> None:
    assert lookup_adr_by_id("ADR-T001", ()) is None


def test_get_adr_registry_returns_deterministic_sample() -> None:
    registry = get_adr_registry()
    assert isinstance(registry, tuple)
    assert len(registry) >= 1
    ids = {adr.decision_id for adr in registry}
    assert "ADR-0001" in ids
    assert "ADR-0002" in ids
    # Deterministic: same result on repeated calls
    assert get_adr_registry() == registry


def test_cli_architecture_decisions_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["architecture", "decisions"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Architecture decisions" in output
    assert "Decision count:" in output
    assert "ADR-0001" in output
    assert "ADR-0002" in output
    assert ADR_INSPECTION_ADVISORY in output


def test_cli_architecture_decisions_json_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["architecture", "decisions", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "decision_count" in data
    assert "decisions" in data
    assert "advisory" in data
    assert data["decision_count"] == len(data["decisions"])
    assert data["advisory"] == ADR_INSPECTION_ADVISORY
    ids = [d["decision_id"] for d in data["decisions"]]
    assert "ADR-0001" in ids
    assert "ADR-0002" in ids


def test_cli_architecture_decisions_json_decision_shape(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    main(["architecture", "decisions", "--json"])
    data = json.loads(capsys.readouterr().out)
    for decision in data["decisions"]:
        assert set(decision) == {
            "decision_id", "title", "status", "rationale",
            "alternatives_considered", "consequences", "created_at",
            "phase_reference", "author", "contributors", "is_human_approved",
        }


def test_cli_architecture_show_human_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["architecture", "show", "ADR-0001"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Architecture decision: ADR-0001" in output
    assert "Title:" in output
    assert "Status:" in output
    assert "Rationale:" in output
    assert "Alternatives considered:" in output
    assert "Consequences:" in output
    assert "Created at:" in output
    assert "Phase reference:" in output
    assert "Author:" in output
    assert "Contributors:" in output
    assert ADR_INSPECTION_ADVISORY in output


def test_cli_architecture_show_json_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["architecture", "show", "ADR-0001", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["decision_id"] == "ADR-0001"
    assert data["title"] == "Use TOML for PCAE policy configuration"
    assert data["status"] == "accepted"
    assert data["is_human_approved"] is True
    assert data["phase_reference"] == "1A"
    assert data["author"] == "atila"
    assert isinstance(data["alternatives_considered"], list)
    assert isinstance(data["consequences"], list)
    assert isinstance(data["contributors"], list)


def test_cli_architecture_show_unknown_id_fails_clearly(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["architecture", "show", "ADR-DOES-NOT-EXIST"])
    output = capsys.readouterr().out
    assert exit_code == 1
    assert "not found" in output
    assert "ADR-DOES-NOT-EXIST" in output


def test_cli_architecture_decisions_does_not_modify_artifacts(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    before = list(tmp_path.iterdir())
    assert main(["architecture", "decisions"]) == 0
    capsys.readouterr()
    assert list(tmp_path.iterdir()) == before
