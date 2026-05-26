from __future__ import annotations

import json
from pathlib import Path

from pcae.cli import main
from pcae.core.provenance import (
    PROVENANCE_HISTORY_RELATIVE_PATH,
    append_provenance_event,
    read_provenance_history,
    read_provenance_status,
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
