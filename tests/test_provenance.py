from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess

from pcae.cli import main
from pcae.core.provenance import (
    PROVENANCE_EXPORTS_RELATIVE_PATH,
    PROVENANCE_HISTORY_RELATIVE_PATH,
    append_provenance_event,
    read_provenance_history,
    read_provenance_status,
    write_provenance_export,
)
from pcae.core.paths import HarnessPath


# ---------------------------------------------------------------------------
# status — no file
# ---------------------------------------------------------------------------


def test_provenance_status_absent(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["provenance", "status"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "File: absent" in output
    assert "Event count: 0" in output
    assert "Latest event: none" in output


# ---------------------------------------------------------------------------
# status — file present with events
# ---------------------------------------------------------------------------


def test_provenance_status_with_events(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    root = HarnessPath(tmp_path)
    append_provenance_event(root, "test.event", "first summary")
    append_provenance_event(root, "test.event", "second summary")

    exit_code = main(["provenance", "status"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "File: present" in output
    assert "Event count: 2" in output
    assert "Latest event: second summary" in output


# ---------------------------------------------------------------------------
# history — no file
# ---------------------------------------------------------------------------


def test_provenance_history_absent(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["provenance", "history"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Event count: 0" in output
    assert "No provenance events recorded." in output


# ---------------------------------------------------------------------------
# history — file present with events
# ---------------------------------------------------------------------------


def test_provenance_history_with_events(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    root = HarnessPath(tmp_path)
    append_provenance_event(root, "session.start", "session started")
    append_provenance_event(root, "session.end", "session ended")

    exit_code = main(["provenance", "history"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Event count: 2" in output
    assert "session.start" in output
    assert "session started" in output
    assert "session.end" in output
    assert "session ended" in output


# ---------------------------------------------------------------------------
# history --json — no file
# ---------------------------------------------------------------------------


def test_provenance_history_json_absent(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["provenance", "history", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    parsed = json.loads(output)
    assert parsed == []


# ---------------------------------------------------------------------------
# history --json — file present
# ---------------------------------------------------------------------------


def test_provenance_history_json_with_events(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    root = HarnessPath(tmp_path)
    append_provenance_event(root, "docs.glossary", "generated GLOSSARY.md")

    exit_code = main(["provenance", "history", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    parsed = json.loads(output)
    assert isinstance(parsed, list)
    assert len(parsed) == 1
    event = parsed[0]
    assert event["event_type"] == "docs.glossary"
    assert event["summary"] == "generated GLOSSARY.md"
    assert "timestamp" in event
    assert "agent_id" in event
    assert "active_task" in event
    assert "git_branch" in event


# ---------------------------------------------------------------------------
# append_provenance_event — round-trip
# ---------------------------------------------------------------------------


def test_append_provenance_event_round_trip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    root = HarnessPath(tmp_path)

    event = append_provenance_event(root, "check.passed", "pcae check passed")

    assert event.event_type == "check.passed"
    assert event.summary == "pcae check passed"
    assert event.timestamp != ""

    history = read_provenance_history(root)
    assert len(history.events) == 1
    assert history.events[0].event_type == "check.passed"


def test_append_provenance_event_accumulates(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    root = HarnessPath(tmp_path)

    append_provenance_event(root, "a", "first")
    append_provenance_event(root, "b", "second")
    append_provenance_event(root, "c", "third")

    history = read_provenance_history(root)
    assert len(history.events) == 3
    assert history.events[0].event_type == "a"
    assert history.events[2].event_type == "c"


# ---------------------------------------------------------------------------
# provenance file is written to .pcae/
# ---------------------------------------------------------------------------


def test_provenance_file_written_to_pcae_directory(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    root = HarnessPath(tmp_path)
    append_provenance_event(root, "test", "summary")

    expected = tmp_path / ".pcae" / "provenance-history.json"
    assert expected.is_file()
    data = json.loads(expected.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) == 1


# ---------------------------------------------------------------------------
# read_provenance_status — absent
# ---------------------------------------------------------------------------


def test_read_provenance_status_absent(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    root = HarnessPath(tmp_path)
    status = read_provenance_status(root)
    assert not status.exists
    assert status.event_count == 0
    assert status.latest_summary is None
    assert status.relative_path == PROVENANCE_HISTORY_RELATIVE_PATH


# ---------------------------------------------------------------------------
# provenance record command
# ---------------------------------------------------------------------------


def test_provenance_record_creates_file_and_appends(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["provenance", "record", "--event-type", "phase_completed", "--summary", "Phase 31B done"]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "phase_completed" in output
    assert "Phase 31B done" in output
    assert (tmp_path / ".pcae" / "provenance-history.json").is_file()


def test_provenance_record_event_visible_in_status(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    main(["provenance", "record", "--event-type", "session.start", "--summary", "session opened"])
    capsys.readouterr()

    exit_code = main(["provenance", "status"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "File: present" in output
    assert "Event count: 1" in output
    assert "Latest event: session opened" in output


def test_provenance_record_event_visible_in_history(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    main(["provenance", "record", "--event-type", "check.passed", "--summary", "all checks ok"])
    capsys.readouterr()

    exit_code = main(["provenance", "history"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "check.passed" in output
    assert "all checks ok" in output


def test_provenance_record_event_visible_in_history_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    main(["provenance", "record", "--event-type", "docs.generated", "--summary", "glossary written"])
    capsys.readouterr()

    exit_code = main(["provenance", "history", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    parsed = json.loads(output)
    assert len(parsed) == 1
    assert parsed[0]["event_type"] == "docs.generated"
    assert parsed[0]["summary"] == "glossary written"


def test_provenance_record_accumulates_multiple_events(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    main(["provenance", "record", "--event-type", "a", "--summary", "first"])
    main(["provenance", "record", "--event-type", "b", "--summary", "second"])
    main(["provenance", "record", "--event-type", "c", "--summary", "third"])
    capsys.readouterr()

    exit_code = main(["provenance", "history", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    parsed = json.loads(output)
    assert len(parsed) == 3
    assert parsed[0]["event_type"] == "a"
    assert parsed[2]["event_type"] == "c"


def test_provenance_record_requires_event_type(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    import pytest
    with pytest.raises(SystemExit) as exc_info:
        main(["provenance", "record", "--summary", "missing event type"])
    assert exc_info.value.code != 0


def test_provenance_record_requires_summary(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    import pytest
    with pytest.raises(SystemExit) as exc_info:
        main(["provenance", "record", "--event-type", "test"])
    assert exc_info.value.code != 0


# ---------------------------------------------------------------------------
# provenance history filtering
# ---------------------------------------------------------------------------


def test_history_filter_by_event_type(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    root = HarnessPath(tmp_path)
    append_provenance_event(root, "agent_acquired", "lock acquired")
    append_provenance_event(root, "phase_completed", "phase done")
    append_provenance_event(root, "agent_acquired", "lock acquired again")

    exit_code = main(["provenance", "history", "--event-type", "agent_acquired"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Event count: 2" in output
    assert "agent_acquired" in output
    assert "phase_completed" not in output


def test_history_filter_by_agent_id(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    root = HarnessPath(tmp_path)
    append_provenance_event(root, "a", "from alice", agent_id="alice")
    append_provenance_event(root, "b", "from bob", agent_id="bob")
    append_provenance_event(root, "c", "from alice again", agent_id="alice")

    exit_code = main(["provenance", "history", "--agent-id", "alice"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Event count: 2" in output
    assert "from alice" in output
    assert "from bob" not in output


def test_history_filter_combined_and_semantics(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    root = HarnessPath(tmp_path)
    append_provenance_event(root, "deploy", "deploy by alice", agent_id="alice")
    append_provenance_event(root, "deploy", "deploy by bob", agent_id="bob")
    append_provenance_event(root, "check", "check by alice", agent_id="alice")

    exit_code = main(
        ["provenance", "history", "--event-type", "deploy", "--agent-id", "alice"]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Event count: 1" in output
    assert "deploy by alice" in output
    assert "deploy by bob" not in output
    assert "check by alice" not in output


def test_history_filter_json_event_type(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    root = HarnessPath(tmp_path)
    append_provenance_event(root, "agent_acquired", "lock acquired")
    append_provenance_event(root, "phase_completed", "phase done")

    exit_code = main(
        ["provenance", "history", "--json", "--event-type", "phase_completed"]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    parsed = json.loads(output)
    assert len(parsed) == 1
    assert parsed[0]["event_type"] == "phase_completed"


def test_history_filter_json_agent_id(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    root = HarnessPath(tmp_path)
    append_provenance_event(root, "a", "from alice", agent_id="alice")
    append_provenance_event(root, "b", "from bob", agent_id="bob")

    exit_code = main(["provenance", "history", "--json", "--agent-id", "bob"])

    output = capsys.readouterr().out
    assert exit_code == 0
    parsed = json.loads(output)
    assert len(parsed) == 1
    assert parsed[0]["agent_id"] == "bob"


def test_history_filter_no_matching_events(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    root = HarnessPath(tmp_path)
    append_provenance_event(root, "agent_acquired", "lock acquired")

    exit_code = main(["provenance", "history", "--event-type", "nonexistent"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Event count: 0" in output
    assert "No matching events." in output


def test_history_filter_json_combined_empty(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    root = HarnessPath(tmp_path)
    append_provenance_event(root, "a", "event", agent_id="alice")

    exit_code = main(
        ["provenance", "history", "--json", "--event-type", "a", "--agent-id", "bob"]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert json.loads(output) == []


def test_history_unfiltered_unchanged(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    root = HarnessPath(tmp_path)
    append_provenance_event(root, "x", "first")
    append_provenance_event(root, "y", "second")

    exit_code = main(["provenance", "history"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Event count: 2" in output
    assert "first" in output
    assert "second" in output


def test_filter_events_core_function(tmp_path: Path, monkeypatch) -> None:
    from pcae.core.provenance import filter_events, ProvenanceEvent
    events = (
        ProvenanceEvent("t1", "a", "alice", None, None, "s1"),
        ProvenanceEvent("t2", "b", "bob", None, None, "s2"),
        ProvenanceEvent("t3", "a", "bob", None, None, "s3"),
    )
    assert len(filter_events(events)) == 3
    assert len(filter_events(events, event_type="a")) == 2
    assert len(filter_events(events, agent_id="bob")) == 2
    assert len(filter_events(events, event_type="a", agent_id="bob")) == 1
    assert len(filter_events(events, event_type="z")) == 0


# ---------------------------------------------------------------------------
# provenance export command
# ---------------------------------------------------------------------------


def test_provenance_export_command_creates_file(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    append_provenance_event(HarnessPath(tmp_path), "test", "an event")

    exit_code = main(["provenance", "export"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Wrote provenance export: .pcae/provenance-exports/provenance-export-" in output
    assert "Event count: 1" in output
    exports = list((tmp_path / ".pcae" / "provenance-exports").glob("*.json"))
    assert len(exports) == 1


def test_provenance_export_with_no_history_exports_empty_events(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["provenance", "export"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Event count: 0" in output
    exports = list((tmp_path / ".pcae" / "provenance-exports").glob("*.json"))
    assert len(exports) == 1
    data = json.loads(exports[0].read_text(encoding="utf-8"))
    assert data["events"] == []
    assert data["event_count"] == 0


def test_provenance_export_json_mode(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    append_provenance_event(HarnessPath(tmp_path), "phase_completed", "done")

    exit_code = main(["provenance", "export", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    parsed = json.loads(output)
    assert parsed["event_count"] == 1
    assert "exported_at" in parsed
    assert "path" in parsed
    assert parsed["path"].startswith(".pcae/provenance-exports/provenance-export-")
    assert "active_task" in parsed
    assert "git_branch" in parsed


def test_provenance_export_bundle_contains_required_keys(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    root = HarnessPath(tmp_path)
    append_provenance_event(root, "a", "first")
    append_provenance_event(root, "b", "second")

    bundle = write_provenance_export(root)

    assert set(bundle.data) == {"active_task", "event_count", "events", "exported_at", "git_branch"}
    assert bundle.data["event_count"] == 2
    assert len(bundle.data["events"]) == 2
    assert isinstance(bundle.data["exported_at"], str)


def test_provenance_export_deterministic_filename(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    root = HarnessPath(tmp_path)
    fixed_time = datetime(2026, 5, 26, 14, 30, 45, tzinfo=timezone.utc)

    bundle = write_provenance_export(root, exported_at=fixed_time)

    assert bundle.relative_path.as_posix() == (
        ".pcae/provenance-exports/provenance-export-20260526-143045.json"
    )
    assert bundle.data["exported_at"] == "2026-05-26T14:30:45+00:00"
    assert (tmp_path / bundle.relative_path).is_file()


def test_provenance_export_artifact_is_gitignored(
    tmp_path: Path, monkeypatch
) -> None:
    init_git_repo(tmp_path)
    pcae_gitignore = tmp_path / ".pcae" / ".gitignore"
    pcae_gitignore.parent.mkdir(parents=True, exist_ok=True)
    pcae_gitignore.write_text(
        "session.json\narchitecture-history.json\nagent-lock.json\n"
        "provenance-history.json\nprovenance-exports/\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    root = HarnessPath(tmp_path)
    bundle = write_provenance_export(root)

    ignored = subprocess.run(
        ["git", "check-ignore", bundle.relative_path.as_posix()],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert ignored.returncode == 0


def init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=root, check=True, capture_output=True, text=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=root, check=True, capture_output=True, text=True,
    )
