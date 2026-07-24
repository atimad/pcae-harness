"""Audit Recorder (IWC-001 v1.1 §13, Phase 143J §16, Phase 143M).

The sole production owner of audit event creation, audit ordering, and
audit serialization for a single Decision Session (Phase 143J §16 Audit
Recorder row: "Owns log completeness and structural separation only").

Append-only: ``AuditRecorder`` exposes no method that mutates or removes
an already-appended ``AuditEvent``. Ordering is deterministic and
sequence-based -- append order -- which is sufficient and correct here
because, unlike Evidence (whose two independently-run assemblies must
converge on identical content-derived ordering, IWC-REQ-079), an audit
log's ordering *is* the append sequence by definition (IWC-001 v1.1 §13:
"what happened, in what order").

This recorder does not, and per its governing phase prompt never will,
publish, notify, create a phase/CHGR report, or create a CHGR. Those
methods do not exist on this class.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from pcae.interactive_workflow.audit.models import AuditEvent
from pcae.interactive_workflow.errors import DuplicateAuditEventError
from pcae.interactive_workflow.session.identity import validate_session_id


class AuditRecorder:
    """Appends and retrieves audit events for exactly one Decision
    Session."""

    def __init__(self, session_id: str) -> None:
        self._session_id = validate_session_id(session_id)
        self._events: Dict[str, AuditEvent] = {}
        self._order: List[str] = []

    @property
    def session_id(self) -> str:
        return self._session_id

    def append(self, event: AuditEvent) -> AuditEvent:
        """Append a new audit event.

        Raises ``DuplicateAuditEventError`` if ``event.event_id`` is
        already present -- the existing entry is never overwritten
        (fail closed, append-only).
        """

        if event.event_id in self._events:
            raise DuplicateAuditEventError(
                f"Audit event identifier {event.event_id!r} is already recorded "
                f"for session {self._session_id!r}."
            )
        self._events[event.event_id] = event
        self._order.append(event.event_id)
        return event

    def get(self, event_id: str) -> Optional[AuditEvent]:
        return self._events.get(event_id)

    def history(self, event_type: Optional[str] = None) -> Tuple[AuditEvent, ...]:
        """Return every appended event, in append order.

        If ``event_type`` is given, the result is filtered to events of
        that type, order preserved -- this supports IWC-001 v1.1 §13.1's
        requirement that a verifier be able to reconstruct each auditable
        boundary independently, without introducing any capability to
        reorder, merge, or summarize events.
        """

        events = tuple(self._events[event_id] for event_id in self._order)
        if event_type is None:
            return events
        return tuple(event for event in events if event.event_type == event_type)


__all__ = ["AuditRecorder"]
