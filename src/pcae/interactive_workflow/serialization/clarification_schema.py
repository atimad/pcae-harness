"""Deterministic wire representation of a ``Clarification`` (Phase 143M).

Mirrors ``pcae.interactive_workflow.serialization.schema``'s discipline
for ``Session``. Does not serialize Preview Digest, confirmation,
publication, or CHGR content -- none of those fields exist on
``Clarification``.
"""

from __future__ import annotations

from typing import Any, Dict

from pcae.interactive_workflow.clarification.models import (
    CLARIFICATION_SCHEMA_VERSION,
    Clarification,
    ClarificationState,
)
from pcae.interactive_workflow.errors import (
    SerializationFailureError,
    UnsupportedVersionError,
)

_KNOWN_SCHEMA_VERSIONS = frozenset({CLARIFICATION_SCHEMA_VERSION})


def to_payload(clarification: Clarification) -> Dict[str, Any]:
    try:
        return {
            "schema_version": CLARIFICATION_SCHEMA_VERSION,
            "clarification_id": clarification.clarification_id,
            "request_text": clarification.request_text,
            "requested_at": clarification.requested_at,
            "lifecycle_state": clarification.lifecycle_state.value,
            "response_text": clarification.response_text,
            "responded_at": clarification.responded_at,
            "tags": list(clarification.tags),
        }
    except AttributeError as exc:
        raise SerializationFailureError(f"Clarification could not be serialized: {exc}") from exc


def from_payload(payload: Dict[str, Any]) -> Clarification:
    schema_version = payload.get("schema_version")
    if schema_version not in _KNOWN_SCHEMA_VERSIONS:
        raise UnsupportedVersionError(
            f"Unsupported Clarification schema_version: {schema_version!r}."
        )

    try:
        return Clarification(
            clarification_id=payload["clarification_id"],
            request_text=payload["request_text"],
            requested_at=payload["requested_at"],
            lifecycle_state=ClarificationState(payload["lifecycle_state"]),
            response_text=payload.get("response_text"),
            responded_at=payload.get("responded_at"),
            tags=tuple(payload.get("tags", ())),
        )
    except (KeyError, ValueError, TypeError) as exc:
        raise SerializationFailureError(f"Clarification payload malformed: {exc}") from exc


__all__ = [
    "CLARIFICATION_SCHEMA_VERSION",
    "to_payload",
    "from_payload",
]
