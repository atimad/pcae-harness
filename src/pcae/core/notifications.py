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
            # Phase 92D.5 trust contract metadata
            "report_completeness": report.report_completeness,
            "missing_trust_fields": report.missing_trust_fields,
            "trust_warnings": report.trust_warnings,
            "pushed_status": report.pushed_status,
            "origin_main_head_count": report.origin_main_head_count,
            "commits": report.commits,
            "files_changed": report.files_changed,
            "tests_run": report.tests_run,
            "explicit_no_go_confirmations": report.explicit_no_go_confirmations,
            "notification_result": report.notification_result,
        },
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════════════
# Telegram outbound sink — Phase 92C
# ═══════════════════════════════════════════════════════════════════════════════

TELEGRAM_SINK_NAME = "telegram"

# Configuration from environment variables only
_TELEGRAM_BOT_TOKEN_ENV = "PCAE_TELEGRAM_BOT_TOKEN"
_TELEGRAM_CHAT_ID_ENV = "PCAE_TELEGRAM_CHAT_ID"
_TELEGRAM_ENABLED_ENV = "PCAE_TELEGRAM_ENABLED"
_DEFAULT_MAX_MESSAGE_CHARS = 3500


class TelegramSink:
    """Outbound Telegram notification sink.

    Sends a short summary via sendMessage and the full report as a
    document via sendDocument.  Uses Python standard library urllib.

    Reads configuration from environment variables only:
      PCAE_TELEGRAM_BOT_TOKEN  — Telegram Bot API token
      PCAE_TELEGRAM_CHAT_ID    — Target chat ID
      PCAE_TELEGRAM_ENABLED    — Optional, defaults to disabled if unset

    No inbound commands.  No polling.  No remote shell.
    """

    def __init__(
        self,
        bot_token: str | None = None,
        chat_id: str | None = None,
        enabled: bool | None = None,
        max_message_chars: int = _DEFAULT_MAX_MESSAGE_CHARS,
        _opener: object = None,  # for test injection
    ):
        import os
        self._bot_token = bot_token if bot_token is not None else os.environ.get(_TELEGRAM_BOT_TOKEN_ENV, "")
        self._chat_id = chat_id if chat_id is not None else os.environ.get(_TELEGRAM_CHAT_ID_ENV, "")
        self._max_message_chars = max_message_chars
        self._opener = _opener

        if enabled is None:
            enabled_str = os.environ.get(_TELEGRAM_ENABLED_ENV, "")
            self._enabled = enabled_str.lower() in ("1", "true", "yes")
        else:
            self._enabled = enabled

    def is_configured(self) -> bool:
        return bool(self._bot_token and self._chat_id)

    def is_enabled(self) -> bool:
        return self._enabled and self.is_configured()

    def send(self, event: NotificationEvent) -> NotificationResult:
        if not self.is_enabled():
            return NotificationResult(
                sink_name=TELEGRAM_SINK_NAME,
                success=False,
                message="Telegram is disabled or not configured.",
                event_id=event.event_id,
                attempted_at=_utc_now_iso(),
                error="disabled_or_unconfigured",
            )

        # 1. Send summary via sendMessage
        summary_text = self._build_summary(event)
        msg_result = self._send_message(summary_text)

        if not msg_result["ok"]:
            return NotificationResult(
                sink_name=TELEGRAM_SINK_NAME,
                success=False,
                message=f"sendMessage failed: {msg_result.get('error', 'unknown')}",
                event_id=event.event_id,
                attempted_at=_utc_now_iso(),
                error=f"sendMessage: {msg_result.get('error', 'unknown')}",
            )

        # 2. Send full report document if artifact paths present
        doc_result = {"ok": True}
        if event.artifact_paths:
            for path in event.artifact_paths[:1]:  # send first artifact as document
                doc_result = self._send_document(path)
                break

        success = msg_result["ok"] and doc_result.get("ok", False)
        return NotificationResult(
            sink_name=TELEGRAM_SINK_NAME,
            success=success,
            message=(
                "Telegram: summary sent" +
                (", document sent" if doc_result.get("ok") else ", document failed")
            ),
            event_id=event.event_id,
            attempted_at=_utc_now_iso(),
            error=(None if success else (
                doc_result.get("error") if not doc_result.get("ok")
                else msg_result.get("error")
            )),
            metadata={
                "send_message_ok": msg_result["ok"],
                "send_document_ok": doc_result.get("ok", False),
            },
        )

    def _build_summary(self, event: NotificationEvent) -> str:
        """Build a concise, structured Telegram text summary.

        Phase 92D.7 — precision tightening: trust state near top, compact
        validation/governance, phase commit distinct from recent commits,
        no duplication. Full details in Markdown attachment.
        """
        from pcae.core.phase_reports import (
            COMPLETENESS_COMPLETE, COMPLETENESS_PARTIAL, COMPLETENESS_INCOMPLETE,
        )
        metadata = event.metadata or {}

        phase_id = metadata.get("phase_id", "?")
        phase_name = metadata.get("phase_name", "")
        phase_status = metadata.get("phase_status", "")
        next_phase = metadata.get("recommended_next_phase", "")
        report_phase_id = metadata.get("report_phase_id", "")

        # Trust state with icon
        completeness = metadata.get("report_completeness", "")
        if completeness == COMPLETENESS_COMPLETE:
            trust_line = "complete ✅"
        elif completeness == COMPLETENESS_PARTIAL:
            missing_fields = metadata.get("missing_trust_fields", [])
            if missing_fields:
                trust_line = f"partial ⚠️  Missing: {', '.join(missing_fields)}"
            else:
                trust_line = "partial ⚠️"
        elif completeness == COMPLETENESS_INCOMPLETE:
            trust_line = "incomplete ❌ Manual review required"
        else:
            trust_line = "not assessed"

        lines: list[str] = []

        # ── Header: phase ID + status + name ────────────────────────────
        status_icon = "✅" if phase_status == "completed" else phase_status
        header = f"PCAE Phase {phase_id} {status_icon}"
        if phase_name:
            header += f"\n{phase_name}"
        lines.append(header)

        # Stale-report check (before trust)
        if report_phase_id and report_phase_id != phase_id:
            lines.append(f"⚠️ STALE: event phase={phase_id}, report phase={report_phase_id}")

        # ── Trust state ─────────────────────────────────────────────────
        lines.append(f"Trust: {trust_line}")
        lines.append("")

        # ── Files/Tests ─────────────────────────────────────────────────
        files_changed = metadata.get("files_changed", 0)
        tests_run = metadata.get("tests_run", 0)
        if files_changed > 0:
            lines.append(f"Files changed: {files_changed}")
        if tests_run > 0:
            lines.append(f"Tests added: {tests_run}")

        # ── Validation (compact single-line when possible) ──────────────
        test_results = metadata.get("test_results", {}) or {}
        if test_results:
            parts = [f"{name}: {val}" for name, val in test_results.items()]
            lines.append(f"Tests: {'; '.join(parts)}")

        # ── Governance (compact single-line) ────────────────────────────
        governance = metadata.get("governance_results", {}) or {}
        if governance:
            parts = [f"{name} {val}" for name, val in governance.items()]
            lines.append(f"Governance: {', '.join(parts)}")

        lines.append("")

        # ── Commits: phase commit distinct from recent ──────────────────
        commits = metadata.get("commits", [])
        if commits:
            lines.append(f"Phase commit: {commits[0][:8]}")
            if len(commits) > 1:
                recent_list = [c[:8] for c in commits[1:6]]  # skip phase commit, max 5
                lines.append(f"Recent commits: {', '.join(recent_list)}")
        else:
            lines.append("Phase commit: not captured")

        # ── Push status ─────────────────────────────────────────────────
        pushed = metadata.get("pushed_status", "")
        origin_count = metadata.get("origin_main_head_count", "")
        push_parts = []
        if pushed:
            push_parts.append(pushed)
        if origin_count is not None and origin_count != "":
            push_parts.append(f"origin/main..HEAD {origin_count}")
        if push_parts:
            lines.append(f"Push: {', '.join(push_parts)}")

        # ── Notification dispatch ───────────────────────────────────────
        notif_result = metadata.get("notification_result", {}) or {}
        dispatched = notif_result.get("dispatched", False)
        if dispatched:
            lines.append("Notification: sent via telegram")
        else:
            lines.append("Notification: skipped")

        # ── No-go (one line) ────────────────────────────────────────────
        no_go = metadata.get("explicit_no_go_confirmations", [])
        if isinstance(no_go, list) and no_go:
            # Take first item, truncate
            ng_text = str(no_go[0])
            if len(ng_text) > 120:
                ng_text = ng_text[:117] + "..."
            lines.append(f"No-go: {ng_text}")
        elif isinstance(no_go, str) and no_go:
            lines.append(f"No-go: {no_go[:120]}")

        # ── Next phase ──────────────────────────────────────────────────
        if next_phase:
            lines.append(f"Next: {next_phase}")

        lines.append("")
        lines.append("Full report attached.")

        text = "\n".join(lines)
        if len(text) > self._max_message_chars:
            text = text[:self._max_message_chars - 3] + "..."
        return text

    @staticmethod
    def _extract_validation_lines(message: str) -> list[str]:
        """Extract validation result lines from the summary message."""
        import re
        results: list[str] = []
        patterns = [
            r'(?:shell\s*gate|Shell gate)[:\s]*(\d+/\d+)',
            r'(?:broker|Broker)[:\s]*(\d+/\d+)',
            r'(?:report.*?notification|Report.*?notification)[:\s]*(\d+/\d+)',
            r'(?:fast.green|Fast.green)[:\s]*(\d+/\d+)',
            r'(?:health|Health)[:\s]*(healthy|unhealthy)',
            r'(?:check|Check)[:\s]*(passed|failed)',
            r'(?:push\s*check|Push check)[:\s]*(nothing_to_push|not_ready|clean)',
            r'(?:origin/main\.\.HEAD)[:\s]*(\d+)',
        ]
        for pattern in patterns:
            m = re.search(pattern, message, re.IGNORECASE)
            if m:
                results.append(m.group(0))
        return results

    def _send_message(self, text: str) -> dict:
        # Use URL-encoded form data matching known-good curl behavior.
        # No parse_mode — plain text avoids Markdown/HTML parse errors
        # (e.g. [INFO] brackets in summary text break Markdown parsing).
        from urllib.parse import urlencode
        payload_bytes = urlencode({
            "chat_id": self._chat_id,
            "text": text,
        }).encode()
        return self._api_call_form("sendMessage", payload_bytes)

    def _send_document(self, file_path: str) -> dict:
        import json as _json
        from pathlib import Path as _Path
        path = _Path(file_path)
        if not path.exists():
            return {"ok": False, "error": f"File not found: {file_path}"}

        content = path.read_bytes()
        filename = path.name

        # Multipart form-data for sendDocument
        boundary = "pcaetelegram92c"
        body_lines: list[bytes] = []
        body_lines.append(f"--{boundary}".encode())
        body_lines.append(b'Content-Disposition: form-data; name="chat_id"')
        body_lines.append(b"")
        body_lines.append(self._chat_id.encode())
        body_lines.append(f"--{boundary}".encode())
        body_lines.append(
            f'Content-Disposition: form-data; name="document"; filename="{filename}"'.encode()
        )
        body_lines.append(b"Content-Type: application/octet-stream")
        body_lines.append(b"")
        body_lines.append(content)
        body_lines.append(f"--{boundary}--".encode())

        body = b"\r\n".join(body_lines)
        url = f"{self._api_base()}/sendDocument"

        return self._api_call_multipart(url, body, boundary)

    def _api_base(self) -> str:
        return f"https://api.telegram.org/bot{self._bot_token}"

    def _api_call(self, method: str, payload: dict) -> dict:
        import json as _json
        from urllib.request import Request, urlopen
        from urllib.error import HTTPError, URLError

        url = f"{self._api_base()}/{method}"
        data = _json.dumps(payload).encode()
        req = Request(url, data=data, headers={"Content-Type": "application/json"})

        try:
            opener = self._opener if self._opener else urlopen
            with opener(req) as resp:
                return _json.loads(resp.read())
        except HTTPError as exc:
            # Read Telegram error response body for detailed error description
            error_body = ""
            try:
                error_body = exc.read().decode()
                error_data = _json.loads(error_body)
                telegram_desc = error_data.get("description", "")
                if telegram_desc:
                    return {"ok": False, "error": f"Telegram: {telegram_desc}", "error_body": error_body}
            except Exception:
                pass
            return {"ok": False, "error": f"HTTP {exc.code}: {exc.reason}", "error_body": error_body}
        except URLError as exc:
            return {"ok": False, "error": str(exc)}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def _api_call_form(self, method: str, payload_bytes: bytes) -> dict:
        """Call Telegram API with URL-encoded form data (matching curl -d behavior)."""
        import json as _json
        from urllib.request import Request, urlopen
        from urllib.error import HTTPError, URLError

        url = f"{self._api_base()}/{method}"
        req = Request(
            url, data=payload_bytes,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        try:
            opener = self._opener if self._opener else urlopen
            with opener(req) as resp:
                return _json.loads(resp.read())
        except HTTPError as exc:
            error_body = ""
            try:
                error_body = exc.read().decode()
                error_data = _json.loads(error_body)
                telegram_desc = error_data.get("description", "")
                if telegram_desc:
                    return {"ok": False, "error": f"Telegram: {telegram_desc}", "error_body": error_body}
            except Exception:
                pass
            return {"ok": False, "error": f"HTTP {exc.code}: {exc.reason}", "error_body": error_body}
        except URLError as exc:
            return {"ok": False, "error": str(exc)}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def _api_call_multipart(self, url: str, body: bytes, boundary: str) -> dict:
        import json as _json
        from urllib.request import Request, urlopen
        from urllib.error import HTTPError, URLError

        req = Request(
            url, data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        try:
            opener = self._opener if self._opener else urlopen
            with opener(req) as resp:
                return _json.loads(resp.read())
        except HTTPError as exc:
            error_body = ""
            try:
                error_body = exc.read().decode()
                error_data = _json.loads(error_body)
                telegram_desc = error_data.get("description", "")
                if telegram_desc:
                    return {"ok": False, "error": f"Telegram: {telegram_desc}", "error_body": error_body}
            except Exception:
                pass
            return {"ok": False, "error": f"HTTP {exc.code}: {exc.reason}", "error_body": error_body}
        except URLError as exc:
            return {"ok": False, "error": str(exc)}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
