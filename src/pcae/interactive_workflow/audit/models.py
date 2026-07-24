"""Immutable Audit Event domain model (IWC-001 v1.1 §13, Phase 143M).

An ``AuditEvent`` is append-only Session Audit Evidence: once constructed
it is never mutated, and the ``AuditRecorder`` (``pcae.
interactive_workflow.audit.recorder``) that holds a log of these never
exposes a mutation or deletion path. Each event carries no authority
metadata beyond the session identity it is scoped to -- no confirmation
field, no CHGR reference field, no publication field -- because this
phase implements none of those capabilities (Preview Digest, confirmation,
publication, and CHGR creation are explicit non-goals of Phase 143M).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, Optional


AUDIT_SCHEMA_VERSION = "interactive-workflow-audit/0.1"


def _frozen_payload(value: Optional[Mapping[str, object]]) -> Mapping[str, object]:
    if value is None:
        return MappingProxyType({})
    return MappingProxyType(dict(value))


@dataclass(frozen=True)
class AuditEvent:
    """A single, immutable audit record.

    ``event_type`` is a free-form, caller-supplied label (e.g.
    ``"ai_conversation"``, ``"clarification"``, ``"proposal"``,
    ``"evidence"``) -- this package does not enumerate or restrict the
    seven boundaries IWC-001 v1.1 §13.1 names, since three of them
    (Preview, Confirmation, resulting CHGR) name artifacts this phase
    does not implement; restricting ``event_type`` to a closed set here
    would either omit those boundaries or implement them prematurely.
    """

    event_id: str
    session_id: str
    event_type: str
    timestamp: str
    payload: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))
    schema_version: str = AUDIT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.event_id:
            raise ValueError("AuditEvent.event_id must be non-empty.")
        if not self.session_id:
            raise ValueError("AuditEvent.session_id must be non-empty.")
        if not self.event_type:
            raise ValueError("AuditEvent.event_type must be non-empty.")
        if not self.timestamp:
            raise ValueError("AuditEvent.timestamp must be non-empty.")
        if not self.schema_version:
            raise ValueError("AuditEvent.schema_version must be non-empty.")
        object.__setattr__(self, "payload", _frozen_payload(self.payload))


__all__ = [
    "AUDIT_SCHEMA_VERSION",
    "AuditEvent",
]
