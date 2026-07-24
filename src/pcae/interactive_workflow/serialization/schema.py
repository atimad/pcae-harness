"""Deterministic wire representation of a ``Session`` (Phase 143K).

Fields: ``schema_version``, identity, state, timestamps, a metadata
container, and the Decision Capture fields in 143K's scope. Excluded by
the governing 143K prompt: Preview Digest, evidence, confirmation,
publication, CHGR -- none of those fields exist on ``Session`` (see
``pcae.interactive_workflow.models.session``) so there is nothing to
serialize for them here. ``metadata`` is the sanctioned future-compatible
extension point: a later phase adds fields there before it earns a
dedicated top-level key and a schema-version bump.

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
from pcae.interactive_workflow.models.session import SCHEMA_VERSION, Session, SessionState

_KNOWN_SCHEMA_VERSIONS = frozenset({SCHEMA_VERSION})


def to_payload(session: Session) -> Dict[str, Any]:
    """Serialize ``session`` to a plain, JSON-compatible ``dict``."""

    try:
        return {
            "schema_version": session.schema_version,
            "session_id": session.session_id,
            "owner_identity": session.owner_identity,
            "template_ref": session.template_ref,
            "subject_ref": session.subject_ref,
            "session_state": session.session_state.value,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "human_selection_id": session.human_selection_id,
            "human_rationale_text": session.human_rationale_text,
            "human_conditions_text": session.human_conditions_text,
            "disclosure_acknowledgements": list(session.disclosure_acknowledgements),
            "metadata": dict(session.metadata),
        }
    except AttributeError as exc:
        raise SerializationFailureError(f"Session could not be serialized: {exc}") from exc


def from_payload(payload: Dict[str, Any]) -> Session:
    """Deserialize a plain ``dict`` (e.g. parsed JSON) into a ``Session``.

    Raises ``UnsupportedVersionError`` for any ``schema_version`` this
    package does not explicitly recognize -- never assumes "latest" as a
    fallback. Raises ``SerializationFailureError`` for any other
    structural defect (missing required key, wrong type).
    """

    schema_version = payload.get("schema_version")
    if schema_version not in _KNOWN_SCHEMA_VERSIONS:
        raise UnsupportedVersionError(
            f"Unsupported Session schema_version: {schema_version!r}."
        )

    try:
        session_state = SessionState(payload["session_state"])
        return Session(
            session_id=payload["session_id"],
            owner_identity=payload["owner_identity"],
            template_ref=payload["template_ref"],
            subject_ref=payload["subject_ref"],
            session_state=session_state,
            schema_version=schema_version,
            created_at=payload["created_at"],
            updated_at=payload["updated_at"],
            human_selection_id=payload.get("human_selection_id"),
            human_rationale_text=payload.get("human_rationale_text"),
            human_conditions_text=payload.get("human_conditions_text"),
            disclosure_acknowledgements=tuple(payload.get("disclosure_acknowledgements", ())),
            metadata=payload.get("metadata", {}),
        )
    except (KeyError, ValueError, TypeError) as exc:
        raise SerializationFailureError(f"Session payload malformed: {exc}") from exc


__all__ = [
    "SCHEMA_VERSION",
    "to_payload",
    "from_payload",
]
