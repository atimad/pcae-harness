"""Deterministic wire representation of a ``Preview`` (Phase 143N).

Uses the generic ``SerializationFailureError`` (not a Preview-specific
subclass), matching Phase 143K's ``Session`` serializer precedent rather
than Phase 143M's ``AuditSerializationFailureError`` split -- this
phase's governing prompt names ``ConfirmationSerializationFailureError``
explicitly for the confirmation models but names no Preview-specific
error, so no new error class is introduced beyond what the prompt itself
requires. Does not serialize CHGR, publication, or execution state --
none of those fields exist on ``Preview`` (see
``pcae.interactive_workflow.preview.models``).

``to_payload``/``from_payload`` perform no partial writes: either the
full payload round-trips or a ``SerializationFailureError`` /
``UnsupportedVersionError`` is raised with no side effect.
"""

from __future__ import annotations

from typing import Any, Dict

from pcae.interactive_workflow.errors import (
    SerializationFailureError,
    UnsupportedVersionError,
)
from pcae.interactive_workflow.preview.models import PREVIEW_SCHEMA_VERSION, Preview

_KNOWN_SCHEMA_VERSIONS = frozenset({PREVIEW_SCHEMA_VERSION})


def to_payload(preview: Preview) -> Dict[str, Any]:
    """Serialize ``preview`` to a plain, JSON-compatible ``dict``."""

    try:
        return {
            "schema_version": preview.schema_version,
            "preview_id": preview.preview_id,
            "session_id": preview.session_id,
            "preview_timestamp": preview.preview_timestamp,
            "transition_sequence_number": preview.transition_sequence_number,
            "evidence_refs": list(preview.evidence_refs),
            "clarification_refs": list(preview.clarification_refs),
            "audit_refs": list(preview.audit_refs),
            "transition_summary": preview.transition_summary,
            "rendered_content": preview.rendered_content,
            "metadata": dict(preview.metadata),
        }
    except AttributeError as exc:
        raise SerializationFailureError(f"Preview could not be serialized: {exc}") from exc


def from_payload(payload: Dict[str, Any]) -> Preview:
    """Deserialize a plain ``dict`` (e.g. parsed JSON) into a ``Preview``.

    Raises ``UnsupportedVersionError`` for any ``schema_version`` this
    package does not explicitly recognize. Raises
    ``SerializationFailureError`` for any other structural defect
    (missing required key, wrong type, or duplicate reference rejected
    by ``Preview``'s own construction discipline surfaced as a
    ``ValueError``).
    """

    schema_version = payload.get("schema_version")
    if schema_version not in _KNOWN_SCHEMA_VERSIONS:
        raise UnsupportedVersionError(f"Unsupported Preview schema_version: {schema_version!r}.")

    try:
        return Preview(
            preview_id=payload["preview_id"],
            session_id=payload["session_id"],
            preview_timestamp=payload["preview_timestamp"],
            transition_sequence_number=payload["transition_sequence_number"],
            evidence_refs=tuple(payload.get("evidence_refs", ())),
            clarification_refs=tuple(payload.get("clarification_refs", ())),
            audit_refs=tuple(payload.get("audit_refs", ())),
            transition_summary=payload.get("transition_summary", ""),
            rendered_content=payload.get("rendered_content", ""),
            metadata=payload.get("metadata", {}),
            schema_version=schema_version,
        )
    except (KeyError, ValueError, TypeError) as exc:
        raise SerializationFailureError(f"Preview payload malformed: {exc}") from exc


__all__ = [
    "PREVIEW_SCHEMA_VERSION",
    "to_payload",
    "from_payload",
]
