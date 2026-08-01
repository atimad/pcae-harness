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

Phase 147O.1 (AESIC-O-01 production wiring) adds ``authority_evaluation_ref``/
``citation_text`` -- the two reference-only fields Phase 143O/145F's own
``PublicationReadinessPackage`` model already defined but this module
never serialized (dead in every persisted artifact until this phase's
production wiring made ``construct_readiness_package`` actually populate
them). Additive and backward compatible: a legacy persisted package with
neither key deserializes with both fields ``None``, identical to today's
behavior (AESIC-REQ-109); ``schema_version`` is unchanged -- this is a
strict superset of the existing wire format, not a new version.
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
    """Serialize ``package`` to a plain, JSON-compatible ``dict``.

    ``authority_evaluation_ref``/``citation_text`` are included only
    when at least one is set (Phase 147O.1): every package built before
    this phase, and every package built by this phase for a session
    where Authority Evaluation stayed disabled/unconfigured, carries
    both as ``None`` and so produces the exact same payload shape (and
    therefore the exact same digest, IWPC-REQ-081/165) as before this
    phase existed -- a genuinely new key here, even holding ``None``,
    would change every legacy package's recomputed digest on next read
    and falsely raise ``PendingReadinessDigestMismatchError``.
    """

    try:
        payload = {
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
            "decision_subject": package.decision_subject,
            "template_id": package.template_id,
            "template_version": package.template_version,
            "selected_option_id": package.selected_option_id,
            "rationale_text": package.rationale_text,
            "conditions_text": package.conditions_text,
            "options_presented": list(package.options_presented),
            "decision_maker_identity_evidence": dict(package.decision_maker_identity_evidence),
            "preview_rendered_content": package.preview_rendered_content,
            "confirmation_statement": package.confirmation_statement,
            "confirmation_timestamp": package.confirmation_timestamp,
            "metadata": dict(package.metadata),
        }
        if package.authority_evaluation_ref is not None or package.citation_text is not None:
            payload["authority_evaluation_ref"] = (
                dict(package.authority_evaluation_ref)
                if package.authority_evaluation_ref is not None
                else None
            )
            payload["citation_text"] = package.citation_text
        return payload
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
            decision_subject=payload.get("decision_subject", ""),
            template_id=payload.get("template_id", ""),
            template_version=payload.get("template_version", ""),
            selected_option_id=payload.get("selected_option_id", ""),
            rationale_text=payload.get("rationale_text"),
            conditions_text=payload.get("conditions_text"),
            options_presented=tuple(payload.get("options_presented", ())),
            decision_maker_identity_evidence=payload.get("decision_maker_identity_evidence", {}),
            preview_rendered_content=payload.get("preview_rendered_content", ""),
            confirmation_statement=payload.get("confirmation_statement", ""),
            confirmation_timestamp=payload.get("confirmation_timestamp", ""),
            metadata=payload.get("metadata", {}),
            authority_evaluation_ref=payload.get("authority_evaluation_ref"),
            citation_text=payload.get("citation_text"),
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
