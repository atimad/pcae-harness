"""Pluggable notification foundation — Phase 92B.

Generic notification event/sink/dispatcher model for PCAE Production v1.
Supports multiple sinks (noop, stdout, filesystem, mock) with fail-continue
dispatch.  Prepares for 92C Telegram delivery without implementing it.

No external network calls. No Telegram. No automatic hooks. No enforcement.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol


SCHEMA_VERSION = "1.0"

# ── Event types ──────────────────────────────────────────────────────────────

EVENT_TYPE_PHASE_REPORT_CREATED = "phase_report_created"
EVENT_TYPE_PHASE_COMPLETED = "phase_completed"
EVENT_TYPE_PHASE_FAILED = "phase_failed"
EVENT_TYPE_MANUAL_TEST = "manual_test"

VALID_EVENT_TYPES: frozenset[str] = frozenset({
    EVENT_TYPE_PHASE_REPORT_CREATED,
    EVENT_TYPE_PHASE_COMPLETED,
    EVENT_TYPE_PHASE_FAILED,
    EVENT_TYPE_MANUAL_TEST,
})

# ── Severities ───────────────────────────────────────────────────────────────

SEVERITY_INFO = "info"
SEVERITY_WARNING = "warning"
SEVERITY_ERROR = "error"
SEVERITY_CRITICAL = "critical"

VALID_SEVERITIES: frozenset[str] = frozenset({
    SEVERITY_INFO,
    SEVERITY_WARNING,
    SEVERITY_ERROR,
    SEVERITY_CRITICAL,
})


# ═══════════════════════════════════════════════════════════════════════════════
# Notification event
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class NotificationEvent:
    """A notification event to be dispatched to one or more sinks.

    No secrets should be included in title/message by default.
    """

    event_id: str = ""
    event_type: str = ""
    title: str = ""
    message: str = ""
    severity: str = SEVERITY_INFO
    created_at: str = ""
    artifact_paths: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.event_id:
            issues.append("event_id is required")
        if not self.event_type:
            issues.append("event_type is required")
        elif self.event_type not in VALID_EVENT_TYPES:
            issues.append(f"invalid event_type: {self.event_type!r}")
        if not self.title:
            issues.append("title is required")
        if not self.message:
            issues.append("message is required")
        if self.severity not in VALID_SEVERITIES:
            issues.append(f"invalid severity: {self.severity!r}")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "title": self.title,
            "message": self.message,
            "severity": self.severity,
            "created_at": self.created_at,
            "artifact_paths": self.artifact_paths,
            "metadata": self.metadata,
        }


def make_notification_event(
    *,
    event_type: str,
    title: str,
    message: str,
    severity: str = SEVERITY_INFO,
    artifact_paths: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> NotificationEvent:
    """Create a validated notification event.  Raises ValueError on invalid input."""
    event = NotificationEvent(
        event_id=f"ntf-{uuid.uuid4().hex[:12]}",
        event_type=event_type,
        title=title,
        message=message,
        severity=severity,
        created_at=_utc_now_iso(),
        artifact_paths=list(artifact_paths or []),
        metadata=dict(metadata or {}),
    )
    issues = event.validate()
    if issues:
        raise ValueError(f"Invalid notification event: {'; '.join(issues)}")
    return event


# ═══════════════════════════════════════════════════════════════════════════════
# Notification result
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class NotificationResult:
    """Result of dispatching a notification event to a single sink."""

    sink_name: str = ""
    success: bool = False
    message: str = ""
    event_id: str = ""
    attempted_at: str = ""
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sink_name": self.sink_name,
            "success": self.success,
            "message": self.message,
            "event_id": self.event_id,
            "attempted_at": self.attempted_at,
            "error": self.error,
            "metadata": self.metadata,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Sink protocol
# ═══════════════════════════════════════════════════════════════════════════════


class NotificationSink(Protocol):
    """Protocol for notification sinks.

    Each sink accepts a NotificationEvent and returns a NotificationResult.
    Sinks must not raise exceptions for normal failures — they should
    return a failed NotificationResult instead.
    """

    def send(self, event: NotificationEvent) -> NotificationResult: ...


# ═══════════════════════════════════════════════════════════════════════════════
# Noop sink
# ═══════════════════════════════════════════════════════════════════════════════


class NoopSink:
    """Sink that accepts events and returns success with no side effects."""

    def send(self, event: NotificationEvent) -> NotificationResult:
        return NotificationResult(
            sink_name="noop",
            success=True,
            message="Event accepted (noop).",
            event_id=event.event_id,
            attempted_at=_utc_now_iso(),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Stdout / text sink
# ═══════════════════════════════════════════════════════════════════════════════


class StdoutSink:
    """Sink that renders events to formatted text.

    Does not print to stdout by default — returns the rendered text
    in the result message for testability.  Use `write=True` for
    actual stdout output.
    """

    def __init__(self, write: bool = False):
        self._write = write

    def send(self, event: NotificationEvent) -> NotificationResult:
        lines = [
            f"[{event.severity.upper()}] {event.title}",
            f"  Event:   {event.event_id}",
            f"  Type:    {event.event_type}",
            f"  Time:    {event.created_at}",
            f"  Message: {event.message}",
        ]
        if event.artifact_paths:
            lines.append(f"  Artifacts: {', '.join(event.artifact_paths)}")
        text = "\n".join(lines)
        if self._write:
            print(text)
        return NotificationResult(
            sink_name="stdout",
            success=True,
            message=text,
            event_id=event.event_id,
            attempted_at=_utc_now_iso(),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Filesystem sink
# ═══════════════════════════════════════════════════════════════════════════════


class FilesystemSink:
    """Sink that writes notification event and result artifacts to a directory.

    No external network.  Durable local notification audit trail.
    """

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)

    def send(self, event: NotificationEvent) -> NotificationResult:
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            safe_id = event.event_id.replace("/", "-")
            base = f"{ts}-{safe_id}"

            event_path = self.output_dir / f"{base}-event.json"
            event_path.write_text(json.dumps(event.to_dict(), indent=2))

            return NotificationResult(
                sink_name="filesystem",
                success=True,
                message=f"Event written to {event_path}",
                event_id=event.event_id,
                attempted_at=_utc_now_iso(),
                metadata={"event_path": str(event_path)},
            )
        except OSError as exc:
            return NotificationResult(
                sink_name="filesystem",
                success=False,
                message=f"Write failed: {exc}",
                event_id=event.event_id,
                attempted_at=_utc_now_iso(),
                error=str(exc),
            )


# ═══════════════════════════════════════════════════════════════════════════════
# Mock / test sink
# ═══════════════════════════════════════════════════════════════════════════════


class MockSink:
    """Sink that records events in memory for test verification."""

    def __init__(self):
        self.events: list[NotificationEvent] = []

    def send(self, event: NotificationEvent) -> NotificationResult:
        self.events.append(event)
        return NotificationResult(
            sink_name="mock",
            success=True,
            message="Event recorded in memory.",
            event_id=event.event_id,
            attempted_at=_utc_now_iso(),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Dispatcher
# ═══════════════════════════════════════════════════════════════════════════════


def dispatch(
    event: NotificationEvent,
    sinks: list[NotificationSink],
) -> list[NotificationResult]:
    """Dispatch a notification event to one or more sinks.

    One sink failure does not prevent other sinks from being attempted.
    Each sink result is collected.  The dispatcher never raises for
    normal sink failures.

    Returns a list of per-sink results.
    """
    results: list[NotificationResult] = []

    # Validate event first
    issues = event.validate()
    if issues:
        return [NotificationResult(
            sink_name="dispatcher",
            success=False,
            message=f"Event validation failed: {'; '.join(issues)}",
            event_id=event.event_id,
            attempted_at=_utc_now_iso(),
            error="validation_failed",
        )]

    for sink in sinks:
        try:
            result = sink.send(event)
            results.append(result)
        except Exception as exc:
            results.append(NotificationResult(
                sink_name=getattr(sink, "__class__", type(sink)).__name__,
                success=False,
                message=f"Sink raised exception: {exc}",
                event_id=event.event_id,
                attempted_at=_utc_now_iso(),
                error=str(exc),
            ))

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# Phase report integration (prepares for 92C)
# ═══════════════════════════════════════════════════════════════════════════════


def phase_report_to_notification_event(
    report: Any,  # PhaseReport
    artifact_paths: list[str] | None = None,
) -> NotificationEvent:
    """Convert a PhaseReport into a NotificationEvent.

    Prepares for 92C Telegram delivery.  Does not send anything.
    """
    from pcae.core.phase_reports import PhaseReport

    if not isinstance(report, PhaseReport):
        raise TypeError(f"Expected PhaseReport, got {type(report).__name__}")

    title = f"Phase {report.status.upper()}: {report.phase_name}"
    message = report.summary
    severity = (
        SEVERITY_ERROR if report.status == "failed"
        else SEVERITY_WARNING if report.status == "blocked"
        else SEVERITY_INFO
    )
    paths = list(artifact_paths or [])

    return make_notification_event(
        event_type=EVENT_TYPE_PHASE_REPORT_CREATED,
        title=title,
        message=message,
        severity=severity,
        artifact_paths=paths,
        metadata={
            "phase_id": report.phase_id,
            "phase_name": report.phase_name,
            "phase_status": report.status,
            "recommended_next_phase": report.recommended_next_phase,
        },
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
