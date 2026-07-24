"""Deterministic wire representation of a ``PublicationReadinessPackage``
(Phase 143O).

Raises ``PublicationHandoffSerializationError`` (not the generic
``SerializationFailureError``) on any round-trip failure, mirroring Phase
143M/143N's per-artifact-class error-splitting precedent
(``AuditSerializationFailureError``, ``ConfirmationSerializationFailureError``).
Round-trips fully or raises -- no partial write, no silent fallback for
an unrecognized ``schema_version``. Does not serialize CHGR, publication
result, lifecycle authority, or execution state -- none of those fields
exist on ``PublicationReadinessPackage`` (see
``pcae.interactive_workflow.publication_handoff.models``).
"""

from __future__ import annotations

from typing import Any, Dict

from pcae.interactive_workflow.errors import (
    PublicationHandoffSerializationError,
    UnsupportedVersionError,
)
from pcae.interactive_workflow.models.session import SessionState
from pcae.interactive_workflow.publication_handoff.models import (
    PUBLICATION_HANDOFF_SCHEMA_VERSION,
    PublicationReadinessPackage,
)

_KNOWN_SCHEMA_VERSIONS = frozenset({PUBLICATION_HANDOFF_SCHEMA_VERSION})


def to_payload(package: PublicationReadinessPackage) -> Dict[str, Any]:
    """Serialize ``package`` to a plain, JSON-compatible ``dict``."""

    try:
        return {
            "schema_version": package.schema_version,
            "package_id": package.package_id,
            "session_id": package.session_id,
            "session_state": package.session_state.value,
            "transition_sequence_number": package.transition_sequence_number,
            "evidence_refs": list(package.evidence_refs),
            "clarification_refs": list(package.clarification_refs),
            "audit_refs": list(package.audit_refs),
            "preview_id": package.preview_id,
            "preview_digest": package.preview_digest,
            "confirmation_request_id": package.confirmation_request_id,
            "confirmation_response_id": package.confirmation_response_id,
            "built_at": package.built_at,
            "metadata": dict(package.metadata),
        }
    except AttributeError as exc:
        raise PublicationHandoffSerializationError(
            f"PublicationReadinessPackage could not be serialized: {exc}"
        ) from exc


def from_payload(payload: Dict[str, Any]) -> PublicationReadinessPackage:
    """Deserialize a plain ``dict`` into a ``PublicationReadinessPackage``.

    Raises ``UnsupportedVersionError`` for any ``schema_version`` this
    package does not explicitly recognize. Raises
    ``PublicationHandoffSerializationError`` for any other structural
    defect (missing required key, wrong type).
    """

    schema_version = payload.get("schema_version")
    if schema_version not in _KNOWN_SCHEMA_VERSIONS:
        raise UnsupportedVersionError(
            f"Unsupported PublicationReadinessPackage schema_version: {schema_version!r}."
        )
    try:
        return PublicationReadinessPackage(
            package_id=payload["package_id"],
            session_id=payload["session_id"],
            session_state=SessionState(payload["session_state"]),
            transition_sequence_number=payload["transition_sequence_number"],
            evidence_refs=tuple(payload.get("evidence_refs", ())),
            clarification_refs=tuple(payload.get("clarification_refs", ())),
            audit_refs=tuple(payload.get("audit_refs", ())),
            preview_id=payload["preview_id"],
            preview_digest=payload["preview_digest"],
            confirmation_request_id=payload["confirmation_request_id"],
            confirmation_response_id=payload["confirmation_response_id"],
            built_at=payload["built_at"],
            metadata=payload.get("metadata", {}),
            schema_version=schema_version,
        )
    except (KeyError, ValueError, TypeError) as exc:
        raise PublicationHandoffSerializationError(
            f"PublicationReadinessPackage payload malformed: {exc}"
        ) from exc


__all__ = [
    "PUBLICATION_HANDOFF_SCHEMA_VERSION",
    "to_payload",
    "from_payload",
]
