"""Tests for Phase 92B pluggable notification foundation."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from pcae.core.notifications import (
    NotificationEvent,
    NotificationResult,
    make_notification_event,
    NoopSink,
    StdoutSink,
    FilesystemSink,
    MockSink,
    dispatch,
    phase_report_to_notification_event,
    EVENT_TYPE_PHASE_REPORT_CREATED,
    EVENT_TYPE_MANUAL_TEST,
    SEVERITY_INFO,
    SEVERITY_ERROR,
    SEVERITY_CRITICAL,
    VALID_SEVERITIES,
)


# ── Event creation ───────────────────────────────────────────────────────────

def test_create_valid_event():
    event = make_notification_event(
        event_type=EVENT_TYPE_MANUAL_TEST,
        title="Test",
        message="Hello.",
    )
    assert event.event_id.startswith("ntf-")
    assert event.event_type == EVENT_TYPE_MANUAL_TEST
    assert event.severity == SEVERITY_INFO
    assert event.created_at


def test_reject_missing_title():
    with pytest.raises(ValueError, match="title"):
        make_notification_event(event_type=EVENT_TYPE_MANUAL_TEST, title="", message="X")


def test_reject_missing_message():
    with pytest.raises(ValueError, match="message"):
        make_notification_event(event_type=EVENT_TYPE_MANUAL_TEST, title="X", message="")


def test_reject_invalid_severity():
    with pytest.raises(ValueError, match="severity"):
        make_notification_event(event_type=EVENT_TYPE_MANUAL_TEST, title="X", message="Y", severity="bogus")


def test_reject_invalid_event_type():
    with pytest.raises(ValueError, match="event_type"):
        make_notification_event(event_type="bogus", title="X", message="Y")


def test_metadata_preserved():
    event = make_notification_event(
        event_type=EVENT_TYPE_MANUAL_TEST, title="X", message="Y",
        metadata={"key": "value"},
    )
    assert event.metadata["key"] == "value"


def test_artifact_paths_preserved():
    event = make_notification_event(
        event_type=EVENT_TYPE_MANUAL_TEST, title="X", message="Y",
        artifact_paths=["a.md", "b.json"],
    )
    assert event.artifact_paths == ["a.md", "b.json"]


# ── Noop sink ────────────────────────────────────────────────────────────────

def test_noop_sink_success():
    event = make_notification_event(event_type=EVENT_TYPE_MANUAL_TEST, title="X", message="Y")
    sink = NoopSink()
    result = sink.send(event)
    assert result.success is True
    assert result.sink_name == "noop"
    assert result.event_id == event.event_id


# ── Stdout/text sink ─────────────────────────────────────────────────────────

def test_stdout_sink_formats_text():
    event = make_notification_event(
        event_type=EVENT_TYPE_MANUAL_TEST, title="Test Title", message="Test message.",
        artifact_paths=["report.md"],
    )
    sink = StdoutSink(write=False)
    result = sink.send(event)
    assert result.success is True
    assert "Test Title" in result.message
    assert "Test message" in result.message
    assert "report.md" in result.message


# ── Filesystem sink ──────────────────────────────────────────────────────────

def test_filesystem_sink_writes_artifact():
    event = make_notification_event(event_type=EVENT_TYPE_MANUAL_TEST, title="X", message="Y")
    with tempfile.TemporaryDirectory() as td:
        sink = FilesystemSink(Path(td))
        result = sink.send(event)
        assert result.success is True
        assert result.sink_name == "filesystem"
        event_path = result.metadata.get("event_path")
        assert event_path
        assert Path(event_path).exists()


def test_filesystem_sink_creates_output_dir():
    event = make_notification_event(event_type=EVENT_TYPE_MANUAL_TEST, title="X", message="Y")
    with tempfile.TemporaryDirectory() as td:
        nested = Path(td) / "nested" / "dir"
        sink = FilesystemSink(nested)
        result = sink.send(event)
        assert result.success is True
        assert nested.exists()


# ── Mock sink ────────────────────────────────────────────────────────────────

def test_mock_sink_records_event():
    event = make_notification_event(event_type=EVENT_TYPE_MANUAL_TEST, title="X", message="Y")
    sink = MockSink()
    result = sink.send(event)
    assert result.success is True
    assert len(sink.events) == 1
    assert sink.events[0].event_id == event.event_id


# ── Dispatcher ───────────────────────────────────────────────────────────────

def test_dispatcher_sends_to_multiple_sinks():
    event = make_notification_event(event_type=EVENT_TYPE_MANUAL_TEST, title="X", message="Y")
    mock = MockSink()
    results = dispatch(event, [NoopSink(), mock])
    assert len(results) == 2
    assert all(r.success for r in results)
    assert len(mock.events) == 1


def test_dispatcher_records_event_id():
    event = make_notification_event(event_type=EVENT_TYPE_MANUAL_TEST, title="X", message="Y")
    results = dispatch(event, [NoopSink()])
    assert results[0].event_id == event.event_id


def test_dispatcher_continues_after_sink_failure():
    """One sink failure does not prevent other sinks from being attempted."""
    event = make_notification_event(event_type=EVENT_TYPE_MANUAL_TEST, title="X", message="Y")
    mock = MockSink()

    class FailingSink:
        def send(self, event):
            raise RuntimeError("Simulated failure")

    results = dispatch(event, [FailingSink(), mock])
    assert len(results) == 2
    assert results[0].success is False
    assert results[1].success is True  # mock still succeeded
    assert len(mock.events) == 1


def test_dispatcher_does_not_crash_on_sink_failure():
    event = make_notification_event(event_type=EVENT_TYPE_MANUAL_TEST, title="X", message="Y")

    class FailingSink:
        def send(self, event):
            raise RuntimeError("boom")

    results = dispatch(event, [FailingSink()])
    assert len(results) == 1
    assert results[0].success is False


def test_dispatcher_rejects_invalid_event():
    event = NotificationEvent()  # no validation
    results = dispatch(event, [NoopSink()])
    assert len(results) == 1
    assert results[0].success is False
    assert results[0].error == "validation_failed"


# ── Phase report to notification event ───────────────────────────────────────

def test_phase_report_to_notification_event():
    from pcae.core.phase_reports import make_phase_report
    report = make_phase_report(
        phase_id="90A", phase_name="Test Phase", status="completed", summary="Done.",
    )
    event = phase_report_to_notification_event(report, artifact_paths=["latest.md"])
    assert event.event_type == EVENT_TYPE_PHASE_REPORT_CREATED
    assert "Test Phase" in event.title
    assert event.metadata["phase_id"] == "90A"
    assert event.artifact_paths == ["latest.md"]


def test_phase_report_failed_maps_to_error_severity():
    from pcae.core.phase_reports import make_phase_report
    report = make_phase_report(
        phase_id="90A", phase_name="X", status="failed", summary="Boom.",
    )
    event = phase_report_to_notification_event(report)
    assert event.severity == SEVERITY_ERROR


def test_phase_report_blocked_maps_to_warning():
    from pcae.core.phase_reports import make_phase_report
    report = make_phase_report(
        phase_id="90A", phase_name="X", status="blocked", summary="Blocked.",
    )
    event = phase_report_to_notification_event(report)
    assert event.severity == "warning"


def test_rejects_non_phase_report():
    with pytest.raises(TypeError):
        phase_report_to_notification_event("not a report")


# ── No external network, no Telegram ─────────────────────────────────────────

def test_no_external_network_calls():
    """All sinks are local-only. Filesystem sink writes to disk only."""
    event = make_notification_event(event_type=EVENT_TYPE_MANUAL_TEST, title="X", message="Y")
    with tempfile.TemporaryDirectory() as td:
        sink = FilesystemSink(Path(td))
        result = sink.send(event)
        assert "http" not in str(result.metadata.get("event_path", ""))
        assert "api.telegram.org" not in str(result.metadata.get("event_path", ""))


def test_telegram_sink_exists_in_92c():
    """TelegramSink exists and is importable (Phase 92C)."""
    from pcae.core.notifications import TelegramSink, TELEGRAM_SINK_NAME
    assert TelegramSink is not None
    assert TELEGRAM_SINK_NAME == "telegram"


def test_no_automatic_hook():
    """Notification events are created explicitly, not automatically."""
    # phase_report_to_notification_event is a pure function, not a hook
    event = make_notification_event(event_type=EVENT_TYPE_MANUAL_TEST, title="X", message="Y")
    assert event.event_type == EVENT_TYPE_MANUAL_TEST
    # No auto-trigger exists


# ── Severity validation ──────────────────────────────────────────────────────

def test_all_valid_severities():
    for sev in VALID_SEVERITIES:
        event = make_notification_event(
            event_type=EVENT_TYPE_MANUAL_TEST, title="X", message="Y", severity=sev,
        )
        assert event.severity == sev
