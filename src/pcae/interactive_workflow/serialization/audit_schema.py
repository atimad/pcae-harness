"""Deterministic wire representation of an ``AuditEvent`` (Phase 143M).

Raises ``AuditSerializationFailureError`` (not the generic
``SerializationFailureError`` Phase 143K's ``Session`` serializer uses) on
any round-trip failure, so a caller can distinguish which artifact class
failed to serialize. Round-trips fully or raises -- no partial write, no
silent fallback for an unrecognized ``schema_version``.
"""

from __future__ import annotations

from typing import Any, Dict

from pcae.interactive_workflow.audit.models import AUDIT_SCHEMA_VERSION, AuditEvent
from pcae.interactive_workflow.errors import (
    AuditSerializationFailureError,
    UnsupportedVersionError,
)

_KNOWN_SCHEMA_VERSIONS = frozenset({AUDIT_SCHEMA_VERSION})


def to_payload(event: AuditEvent) -> Dict[str, Any]:
    try:
        return {
            "schema_version": event.schema_version,
            "event_id": event.event_id,
            "session_id": event.session_id,
            "event_type": event.event_type,
            "timestamp": event.timestamp,
            "payload": dict(event.payload),
        }
    except AttributeError as exc:
        raise AuditSerializationFailureError(
            f"AuditEvent could not be serialized: {exc}"
        ) from exc


def from_payload(payload: Dict[str, Any]) -> AuditEvent:
    schema_version = payload.get("schema_version")
    if schema_version not in _KNOWN_SCHEMA_VERSIONS:
        raise UnsupportedVersionError(
            f"Unsupported AuditEvent schema_version: {schema_version!r}."
        )

    try:
        return AuditEvent(
            event_id=payload["event_id"],
            session_id=payload["session_id"],
            event_type=payload["event_type"],
            timestamp=payload["timestamp"],
            payload=payload.get("payload", {}),
            schema_version=schema_version,
        )
    except (KeyError, ValueError, TypeError) as exc:
        raise AuditSerializationFailureError(f"AuditEvent payload malformed: {exc}") from exc


__all__ = [
    "AUDIT_SCHEMA_VERSION",
    "to_payload",
    "from_payload",
]
