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
# External-delivery authorization boundary — Phase 134B.2
# ═══════════════════════════════════════════════════════════════════════════════
#
# 134B.1 isolated *ordinary test execution* from live delivery by deleting
# five named environment variables in tests/conftest.py. That protected
# every call site that happened to read exactly those names, but it was not
# an architectural boundary: `pcae notify send-report` (commands.
# notifications.run_notify_send_report) constructs TelegramSink() and calls
# dispatch() directly, honoring only TelegramSink's own internal env check
# -- never PCAE_NOTIFY_ENABLED, the master switch finalize_phase_report()
# uses. Any future adapter wired in the same way (its own env names, its
# own is_enabled()) would inherit that same gap, and the conftest sanitizer
# would need manual, per-adapter extension to keep covering it.
#
# `dispatch()` is the one function every real call site (today and future)
# already goes through, so the fail-closed authorization gate belongs here:
# any sink that is not a known local/no-network sink requires
# PCAE_NOTIFY_ENABLED to be truthy, regardless of which concrete adapter it
# is or what environment-variable names that adapter happens to use. A
# future adapter added to the sink-construction chain inherits this
# automatically -- no sanitizer list to extend, no per-call-site check to
# duplicate.

_LOCAL_SAFE_SINK_TYPES: tuple[type, ...] = (NoopSink, StdoutSink, FilesystemSink, MockSink)


def _requires_external_delivery_authorization(sink: NotificationSink) -> bool:
    """True unless `sink` is a known local/no-network sink.

    Fail-closed by construction: any sink type not explicitly on the local
    allowlist (including one that does not exist yet) is treated as a real
    external-delivery adapter and requires authorization.
    """
    return not isinstance(sink, _LOCAL_SAFE_SINK_TYPES)


def _external_delivery_authorized() -> bool:
    import os
    return os.environ.get("PCAE_NOTIFY_ENABLED", "").lower() in ("1", "true", "yes")


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

    Before any non-local sink is sent to, this function requires
    ``PCAE_NOTIFY_ENABLED`` to be truthy (Phase 134B.2 external-delivery
    authorization boundary) -- transport-independent and enforced before
    adapter-specific behavior runs, so it applies automatically to sinks
    that do not exist yet.

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

    authorized = None  # computed lazily; not every dispatch has a non-local sink
    for sink in sinks:
        if _requires_external_delivery_authorization(sink):
            if authorized is None:
                authorized = _external_delivery_authorized()
            if not authorized:
                results.append(NotificationResult(
                    sink_name=getattr(sink, "__class__", type(sink)).__name__,
                    success=False,
                    message=(
                        "External delivery not authorized: PCAE_NOTIFY_ENABLED "
                        "is not set to 1/true/yes."
                    ),
                    event_id=event.event_id,
                    attempted_at=_utc_now_iso(),
                    error="external_delivery_not_authorized",
                ))
                continue
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
            # Phase 126G — previously omitted here despite TelegramSink's
            # own _build_summary() reading these exact keys, which meant
            # every Telegram summary silently rendered zero governance/
            # test evidence lines regardless of what the canonical report
            # actually contained.
            "test_results": dict(report.test_results),
            "governance_results": dict(report.governance_results),
            "report_consistency": _report_consistency_summary(report),
            # Phase 126G — the exact markdown the trust gate validated,
            # embedded directly so Telegram delivery can never diverge
            # from a possibly-stale sibling file on disk (Consistency
            # Contract: "Telegram content shall be derived directly from
            # the canonical report").
            "canonical_report_markdown": report.render_markdown(),
        },
    )


def _report_consistency_summary(report: Any) -> dict[str, Any]:
    """Compact report-consistency summary for notification metadata.

    Mirrors the same fields PhaseReport.render_markdown()'s own
    "Report Consistency" section already computes, so the notification
    can reflect this without re-deriving different logic.
    """
    consistency_warnings = [
        w for w in report.trust_warnings
        if "Mismatch" in w or "canonical report and metadata" in w
        or "canonical report validation failed" in w
        or "no canonical report artifact" in w
    ]
    canon_present = bool(report.canonical_report_content) or report.canonical_report_used
    return {
        "canonical_report_present": canon_present,
        "status": "mismatch" if consistency_warnings else "consistent",
    }


def phase_report_to_partial_warning_notification_event(
    report: Any,  # PhaseReport
    reason: str,
    artifact_paths: list[str] | None = None,
) -> NotificationEvent:
    """Phase 113X.3 — a clearly-labeled WARNING event for a phase that
    finalized (canonical latest.md/latest.json were written) but whose
    report is not fully trust-complete.

    Distinct in both title and forced ``SEVERITY_WARNING`` from
    ``phase_report_to_notification_event()``'s normal "Phase COMPLETED"
    event, so a partial report is never mistaken on the mobile channel
    for a normal final completion report (105D's rule: partial reports
    are not sent as normal final reports) -- while the operator still
    isn't left silent (113X.3's core governance rule: a finalized phase
    that updates canonical artifacts must never be silent on Telegram).
    """
    from pcae.core.phase_reports import PhaseReport

    if not isinstance(report, PhaseReport):
        raise TypeError(f"Expected PhaseReport, got {type(report).__name__}")

    title = (
        f"PHASE FINALIZED BUT REPORT PARTIAL — mobile operator attention "
        f"required: {report.phase_name} (Phase {report.phase_id})"
    )
    message = f"{report.summary}\n\nReason report is partial: {reason}"
    paths = list(artifact_paths or [])

    return make_notification_event(
        event_type=EVENT_TYPE_PHASE_REPORT_CREATED,
        title=title,
        message=message,
        severity=SEVERITY_WARNING,
        artifact_paths=paths,
        metadata={
            "phase_id": report.phase_id,
            "phase_name": report.phase_name,
            "phase_status": report.status,
            "notification_kind": "partial_warning",
            "partial_reason": reason,
            "report_completeness": report.report_completeness,
            "missing_trust_fields": report.missing_trust_fields,
            "trust_warnings": report.trust_warnings,
            # Phase 126G — a partial report still faithfully carries
            # whatever evidence it does have; only genuinely missing
            # fields should be absent, never present-but-dropped.
            "commits": report.commits,
            "files_changed": report.files_changed,
            "tests_run": report.tests_run,
            "pushed_status": report.pushed_status,
            "origin_main_head_count": report.origin_main_head_count,
            "explicit_no_go_confirmations": report.explicit_no_go_confirmations,
            "recommended_next_phase": report.recommended_next_phase,
            "test_results": dict(report.test_results),
            "governance_results": dict(report.governance_results),
            "report_consistency": _report_consistency_summary(report),
            "canonical_report_markdown": report.render_markdown(),
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


# ═══════════════════════════════════════════════════════════════════════════════
# Durable notification-receipt model — Phase ...1.1R.1R
#
# THE DEFECT THIS REPAIRS: TelegramSink.send() already receives real
# Telegram Bot API JSON responses (``ok``, and on success a ``result``
# Message object carrying ``message_id``) for both the summary and
# document operations, but historically collapsed each into a single
# in-process boolean and discarded the rest. Once the process exits,
# nothing durable on disk can answer "did Telegram actually accept
# this send, and what message_id did it return" -- only an in-memory
# ``NotificationResult.message`` string, printed to the terminal and
# never persisted.
#
# `.pcae/phase-reports/.last-notified.json` (see `_persist_notification_
# result` in phase_reports.py) is a DEDUP MARKER only -- it records
# that PCAE *attempted* dispatch for a given phase/commit/report-digest
# once, not that Telegram *accepted* anything. The separate
# `.pcae/delivery-receipts/` architecture (Phase 134E.7's "External
# Delivery Receipt Model" module) is explicitly documented as "not yet
# active lifecycle authority" -- nothing in the real notification path
# calls into it, and its only registered adapters (`recording_v1`/
# `null_v1`, in its companion delivery-pipeline module) are synthetic/
# no-op (`destination_classification: synthetic_recording`,
# `represents_external_delivery: false`). Wiring a real external
# Telegram adapter into that dormant pipeline would be its own
# separately-scoped "Final Lifecycle Integration" (134E.10, explicitly
# marked not implemented there) -- far beyond this narrowly-scoped
# repair. This module therefore adds the smallest new, purpose-built
# receipt persistence consistent with that architecture's vocabulary
# (attempt identity, durable pre-attempt state, explicit outcome
# classification) without adopting its adapter/pipeline machinery.
# ═══════════════════════════════════════════════════════════════════════════════

#: Closed receipt-status vocabulary (semantic wall preserved: DISPATCH
#: ATTEMPT != TELEGRAM API ACCEPTANCE != DURABLE ACCEPTANCE RECEIPT !=
#: DEVICE PUSH NOTIFICATION != HUMAN OBSERVATION != HUMAN ACKNOWLEDGEMENT.
#: This model proves only up through TELEGRAM API ACCEPTANCE / DURABLE
#: ACCEPTANCE RECEIPT -- never anything past that wall.)
RECEIPT_STATUS_PREPARED = "prepared"
RECEIPT_STATUS_API_ACCEPTED = "api_accepted"
RECEIPT_STATUS_API_REJECTED = "api_rejected"
RECEIPT_STATUS_TRANSPORT_FAILED = "transport_failed"
RECEIPT_STATUS_OUTCOME_UNCERTAIN = "outcome_uncertain"

VALID_RECEIPT_STATUSES: frozenset[str] = frozenset({
    RECEIPT_STATUS_PREPARED,
    RECEIPT_STATUS_API_ACCEPTED,
    RECEIPT_STATUS_API_REJECTED,
    RECEIPT_STATUS_TRANSPORT_FAILED,
    RECEIPT_STATUS_OUTCOME_UNCERTAIN,
})

_RECEIPTS_OUTPUT_DIR_ENV = "PCAE_NOTIFICATION_RECEIPTS_DIR"
_DEFAULT_RECEIPTS_DIR = ".pcae/notification-receipts"
_RECEIPT_SCHEMA_VERSION = "1.0"


def _receipts_root() -> Path:
    import os
    return Path(os.environ.get(_RECEIPTS_OUTPUT_DIR_ENV, _DEFAULT_RECEIPTS_DIR))


def _safe_destination_alias(chat_id: str) -> str:
    """A stable, non-reversible alias for the configured chat -- never
    the raw chat_id, and never any Telegram user/chat profile data
    (name, username), which Telegram's success response can carry but
    this receipt model deliberately never captures (item 8's privacy
    boundary)."""
    import hashlib
    digest = hashlib.sha256(("telegram-chat:" + str(chat_id)).encode("utf-8")).hexdigest()
    return f"telegram:chat:{digest[:12]}"


def _new_receipt_id() -> str:
    return f"ntfr-{uuid.uuid4().hex[:16]}"


def _coerce_http_status(resp: Any) -> int | None:
    """Extract an HTTP status code defensively -- a genuine
    ``http.client.HTTPResponse`` exposes ``.status`` (Python 3.9+) as
    a real ``int``; anything else (a test double lacking it, or one
    whose ``.status``/``.getcode()`` returns something else entirely)
    yields ``None`` rather than persisting a non-serializable or
    fabricated value."""

    for candidate in (getattr(resp, "status", None), getattr(resp, "getcode", lambda: None)()):
        if isinstance(candidate, int) and not isinstance(candidate, bool):
            return candidate
    return None


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.parent / f".{path.name}.tmp"
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    import os
    os.replace(str(tmp_path), str(path))


def _safe_path_component(value: str) -> str:
    import re
    return re.sub(r"[^A-Za-z0-9._-]", "-", str(value or ""))


def _receipt_path(receipt_id: str, event_id: str) -> Path:
    safe_event = _safe_path_component(event_id) or "event"
    return _receipts_root() / safe_event / f"{receipt_id}.json"


def _persist_receipt(receipt: dict[str, Any]) -> "tuple[bool, str | None]":
    """Best-effort durable write. Returns ``(persisted, error)``.

    Never raises -- a receipt-persistence failure must not crash the
    sink (`NotificationSink.send()` must not raise), and per item 39
    an API-accepted-but-unpersisted outcome must not be silently
    treated as safely resendable. Callers surface ``error`` in the
    returned ``NotificationResult`` so the console/audit trail stays
    honest even when durable persistence itself is unavailable."""

    path = _receipt_path(receipt["receipt_id"], receipt["event_id"])
    try:
        _atomic_write_json(path, receipt)
        return True, None
    except OSError as exc:
        # Last-resort, best-effort plain-text fallback so a persistence
        # failure is not entirely invisible -- wrapped so it can never
        # itself raise.
        try:
            fallback = _receipts_root() / "PERSISTENCE-FAILURES.log"
            fallback.parent.mkdir(parents=True, exist_ok=True)
            with open(fallback, "a", encoding="utf-8") as fh:
                fh.write(
                    f"{_utc_now_iso()} receipt_id={receipt.get('receipt_id')} "
                    f"event_id={receipt.get('event_id')} operation={receipt.get('operation')} "
                    f"status={receipt.get('status')} error={exc!r}\n"
                )
        except OSError:
            pass
        return False, str(exc)


def _build_receipt(
    *,
    receipt_id: str,
    event: NotificationEvent,
    operation: str,
    status: str,
    destination_alias: str,
    attempted_at: str,
    recorded_at: str,
    telegram_message_id: int | None = None,
    http_status: int | None = None,
    sanitized_error: str | None = None,
    report_digest_prefix: str | None = None,
) -> dict[str, Any]:
    """Minimum acceptance-receipt content (item 9), scoped to what this
    repair proves and nothing past the semantic wall. Never includes
    the bot token, request headers, or the raw API URL (item 8)."""

    assert operation in ("summary", "document")
    assert status in VALID_RECEIPT_STATUSES
    phase_id = (event.metadata or {}).get("phase_id")
    return {
        "schema": "PCAE-NOTIFICATION-RECEIPT/1.0",
        "schema_version": _RECEIPT_SCHEMA_VERSION,
        "receipt_id": receipt_id,
        "event_id": event.event_id,
        "phase_id": phase_id,
        "report_digest_prefix": report_digest_prefix,
        "sink": TELEGRAM_SINK_NAME,
        "operation": operation,
        "status": status,
        "represents_external_api_acceptance": status == RECEIPT_STATUS_API_ACCEPTED,
        "destination_alias": destination_alias,
        "attempted_at": attempted_at,
        "recorded_at": recorded_at,
        "telegram_message_id": telegram_message_id,
        "http_status": http_status,
        "sanitized_error": sanitized_error,
    }


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

        import hashlib
        destination_alias = _safe_destination_alias(self._chat_id)
        canonical_markdown = (event.metadata or {}).get("canonical_report_markdown")
        report_digest_prefix = (
            hashlib.sha256(canonical_markdown.encode("utf-8")).hexdigest()[:16]
            if canonical_markdown else None
        )
        receipts: dict[str, dict[str, Any]] = {}

        # 1. Send summary via sendMessage
        summary_text = self._build_summary(event)
        summary_receipt_id = _new_receipt_id()
        summary_attempted_at = _utc_now_iso()
        # Pre-attempt durability (item 11): a durable PREPARED record
        # exists before the network call, so a crash mid-request still
        # leaves evidence that an attempt was made under this identity.
        _persist_receipt(_build_receipt(
            receipt_id=summary_receipt_id, event=event, operation="summary",
            status=RECEIPT_STATUS_PREPARED, destination_alias=destination_alias,
            attempted_at=summary_attempted_at, recorded_at=summary_attempted_at,
            report_digest_prefix=report_digest_prefix,
        ))
        msg_result = self._send_message(summary_text)
        summary_status, summary_message_id, summary_http_status, summary_error = (
            self._classify_telegram_result(msg_result)
        )
        summary_recorded_at = _utc_now_iso()
        summary_persisted, summary_persist_err = _persist_receipt(_build_receipt(
            receipt_id=summary_receipt_id, event=event, operation="summary",
            status=summary_status, destination_alias=destination_alias,
            attempted_at=summary_attempted_at, recorded_at=summary_recorded_at,
            telegram_message_id=summary_message_id, http_status=summary_http_status,
            sanitized_error=summary_error, report_digest_prefix=report_digest_prefix,
        ))
        receipts["summary"] = {
            "status": summary_status, "message_id": summary_message_id,
            "receipt_id": summary_receipt_id, "receipt_persisted": summary_persisted,
            "receipt_persist_error": summary_persist_err,
        }

        if not msg_result["ok"]:
            return NotificationResult(
                sink_name=TELEGRAM_SINK_NAME,
                success=False,
                message=f"sendMessage failed: {msg_result.get('error', 'unknown')}",
                event_id=event.event_id,
                attempted_at=_utc_now_iso(),
                error=f"sendMessage: {msg_result.get('error', 'unknown')}",
                metadata={
                    "summary_status": summary_status,
                    "summary_message_id": summary_message_id,
                    "summary_receipt_id": summary_receipt_id,
                    "document_status": None,
                    "document_message_id": None,
                    "document_receipt_id": None,
                    "receipts_dir": str(_receipts_root()),
                },
            )

        # 2. Send the complete canonical report as a document.
        #
        # Fallback contract (Phase 126G), in preferred order:
        #   1. Deliver the complete canonical report if within limits.
        #   2/3. Attach it as a document (Telegram's ~50MB sendDocument
        #      limit comfortably covers every canonical text report this
        #      system produces) alongside the executive-summary message
        #      already sent above.
        #   4. Only if attachment is genuinely impossible, emit a
        #      clearly marked fallback message stating delivery was
        #      incomplete -- never silent.
        #
        # Phase 126G — prefer content embedded directly on the event
        # (``canonical_report_markdown``, populated from the trusted
        # PhaseReport object at event-construction time) over a raw
        # file path, so delivery can never diverge from a possibly
        # stale sibling file on disk (Consistency Contract).
        doc_result = {"ok": True}
        attempted_document = False
        document_status = None
        document_message_id = None
        document_receipt_id = None
        if canonical_markdown:
            attempted_document = True
            phase_id = (event.metadata or {}).get("phase_id") or "report"
            filename = f"{_safe_doc_filename(phase_id)}-phase-report.md"
            document_receipt_id = _new_receipt_id()
            doc_attempted_at = _utc_now_iso()
            _persist_receipt(_build_receipt(
                receipt_id=document_receipt_id, event=event, operation="document",
                status=RECEIPT_STATUS_PREPARED, destination_alias=destination_alias,
                attempted_at=doc_attempted_at, recorded_at=doc_attempted_at,
                report_digest_prefix=report_digest_prefix,
            ))
            doc_result = self._send_document_bytes(
                canonical_markdown.encode("utf-8"), filename=filename,
            )
            document_status, document_message_id, doc_http_status, doc_error = (
                self._classify_telegram_result(doc_result)
            )
            _persist_receipt(_build_receipt(
                receipt_id=document_receipt_id, event=event, operation="document",
                status=document_status, destination_alias=destination_alias,
                attempted_at=doc_attempted_at, recorded_at=_utc_now_iso(),
                telegram_message_id=document_message_id, http_status=doc_http_status,
                sanitized_error=doc_error, report_digest_prefix=report_digest_prefix,
            ))
        elif event.artifact_paths:
            attempted_document = True
            for path in event.artifact_paths[:1]:  # send first artifact as document
                document_receipt_id = _new_receipt_id()
                doc_attempted_at = _utc_now_iso()
                _persist_receipt(_build_receipt(
                    receipt_id=document_receipt_id, event=event, operation="document",
                    status=RECEIPT_STATUS_PREPARED, destination_alias=destination_alias,
                    attempted_at=doc_attempted_at, recorded_at=doc_attempted_at,
                    report_digest_prefix=report_digest_prefix,
                ))
                doc_result = self._send_document(path)
                document_status, document_message_id, doc_http_status, doc_error = (
                    self._classify_telegram_result(doc_result)
                )
                _persist_receipt(_build_receipt(
                    receipt_id=document_receipt_id, event=event, operation="document",
                    status=document_status, destination_alias=destination_alias,
                    attempted_at=doc_attempted_at, recorded_at=_utc_now_iso(),
                    telegram_message_id=document_message_id, http_status=doc_http_status,
                    sanitized_error=doc_error, report_digest_prefix=report_digest_prefix,
                ))
                break

        # Fallback contract item 4 — document attachment failed: send an
        # explicit, clearly marked follow-up message rather than leaving
        # the operator with only a silent "document failed" field in a
        # Python result object nobody on the mobile channel ever sees.
        if attempted_document and not doc_result.get("ok", False):
            self._send_message(
                "⚠️ TRUNCATED — canonical report delivery incomplete.\n"
                f"Document attachment failed: {doc_result.get('error', 'unknown error')}.\n"
                "Only the summary above was delivered; the full canonical "
                "report was not."
            )

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
                "summary_status": summary_status,
                "summary_message_id": summary_message_id,
                "summary_receipt_id": summary_receipt_id,
                "document_status": document_status,
                "document_message_id": document_message_id,
                "document_receipt_id": document_receipt_id,
                "receipts_dir": str(_receipts_root()),
            },
        )

    @staticmethod
    def _classify_telegram_result(
        result: dict[str, Any],
    ) -> "tuple[str, int | None, int | None, str | None]":
        """Classify a raw Telegram API call result into
        ``(status, message_id, http_status, sanitized_error)``.

        Strict validated-response semantics (item 12): ``ok: true``
        without the expected ``result.message_id`` shape is
        ``OUTCOME_UNCERTAIN``, not blindly accepted as
        ``API_ACCEPTED``. ``ok: false`` is either ``API_REJECTED``
        (Telegram itself returned a description) or
        ``TRANSPORT_FAILED`` (no HTTP response was ever received from
        Telegram at all)."""

        http_status = result.get("_http_status")
        if result.get("ok"):
            message_id = (result.get("result") or {}).get("message_id")
            if isinstance(message_id, int):
                return RECEIPT_STATUS_API_ACCEPTED, message_id, http_status, None
            return RECEIPT_STATUS_OUTCOME_UNCERTAIN, None, http_status, "ok_true_without_valid_message_id"

        failure_kind = result.get("_failure_kind")
        sanitized_error = result.get("error")
        if failure_kind == "transport_failed":
            return RECEIPT_STATUS_TRANSPORT_FAILED, None, http_status, sanitized_error
        # api_rejected or http_error: Telegram's own server responded.
        return RECEIPT_STATUS_API_REJECTED, None, http_status, sanitized_error

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

        # ── Report consistency (compact) ────────────────────────────────
        consistency = metadata.get("report_consistency") or {}
        if consistency:
            lines.append(f"Consistency: {consistency.get('status', 'unknown')}")

        # ── Next phase ──────────────────────────────────────────────────
        if next_phase:
            lines.append(f"Next: {next_phase}")

        lines.append("")
        lines.append("Full report attached.")

        text = "\n".join(lines)
        if len(text) > self._max_message_chars:
            # Phase 126G — silent truncation is forbidden (Fallback
            # Contract). Truncate at a safe boundary but always append an
            # explicit, unmissable marker rather than a bare "...", and
            # point the reader at the full canonical report attached
            # separately as a document.
            marker = "\n[TRUNCATED — full canonical report attached as document]"
            keep = max(self._max_message_chars - len(marker), 0)
            text = text[:keep].rstrip() + marker
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
        from pathlib import Path as _Path
        path = _Path(file_path)
        if not path.exists():
            return {"ok": False, "error": f"File not found: {file_path}"}

        return self._send_document_bytes(path.read_bytes(), filename=path.name)

    def _send_document_bytes(self, content: bytes, *, filename: str) -> dict:
        """Send raw bytes as a Telegram document (sendDocument).

        Phase 126G — used to deliver canonical report content embedded
        directly on the event (already-rendered, trusted markdown)
        rather than requiring a file to exist on disk, so delivery can
        never diverge from what the trust gate actually validated.
        """
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
                http_status = _coerce_http_status(resp)
                parsed = _json.loads(resp.read())
                parsed["_http_status"] = http_status
                return parsed
        except HTTPError as exc:
            error_body = ""
            try:
                error_body = exc.read().decode()
                error_data = _json.loads(error_body)
                telegram_desc = error_data.get("description", "")
                if telegram_desc:
                    return {
                        "ok": False, "error": f"Telegram: {telegram_desc}", "error_body": error_body,
                        "_http_status": exc.code, "_failure_kind": "api_rejected",
                    }
            except Exception:
                pass
            return {
                "ok": False, "error": f"HTTP {exc.code}: {exc.reason}", "error_body": error_body,
                "_http_status": exc.code, "_failure_kind": "http_error",
            }
        except URLError as exc:
            return {"ok": False, "error": str(exc), "_http_status": None, "_failure_kind": "transport_failed"}
        except Exception as exc:
            return {"ok": False, "error": str(exc), "_http_status": None, "_failure_kind": "transport_failed"}

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
                http_status = _coerce_http_status(resp)
                parsed = _json.loads(resp.read())
                parsed["_http_status"] = http_status
                return parsed
        except HTTPError as exc:
            error_body = ""
            try:
                error_body = exc.read().decode()
                error_data = _json.loads(error_body)
                telegram_desc = error_data.get("description", "")
                if telegram_desc:
                    return {
                        "ok": False, "error": f"Telegram: {telegram_desc}", "error_body": error_body,
                        "_http_status": exc.code, "_failure_kind": "api_rejected",
                    }
            except Exception:
                pass
            return {
                "ok": False, "error": f"HTTP {exc.code}: {exc.reason}", "error_body": error_body,
                "_http_status": exc.code, "_failure_kind": "http_error",
            }
        except URLError as exc:
            return {"ok": False, "error": str(exc), "_http_status": None, "_failure_kind": "transport_failed"}
        except Exception as exc:
            return {"ok": False, "error": str(exc), "_http_status": None, "_failure_kind": "transport_failed"}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_doc_filename(phase_id: str) -> str:
    """Sanitize a phase_id for use as a Telegram document filename."""
    import re
    return re.sub(r"[^A-Za-z0-9._-]", "-", str(phase_id)) or "report"
