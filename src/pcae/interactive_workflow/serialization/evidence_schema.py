"""Deterministic wire representation of an ``EvidenceItem`` (Phase 143M).

Mirrors ``pcae.interactive_workflow.serialization.schema``'s discipline
for ``Session``: ``to_payload``/``from_payload`` round-trip fully or raise
-- no partial write, no silent fallback to "latest" for an unrecognized
``schema_version``.
"""

from __future__ import annotations

from typing import Any, Dict

from pcae.interactive_workflow.errors import (
    SerializationFailureError,
    UnsupportedVersionError,
)
from pcae.interactive_workflow.evidence.models import (
    EVIDENCE_SCHEMA_VERSION,
    EvidenceAvailability,
    EvidenceItem,
)

_KNOWN_SCHEMA_VERSIONS = frozenset({EVIDENCE_SCHEMA_VERSION})


def to_payload(item: EvidenceItem) -> Dict[str, Any]:
    try:
        return {
            "schema_version": EVIDENCE_SCHEMA_VERSION,
            "evidence_id": item.evidence_id,
            "evidence_type": item.evidence_type,
            "provenance_ref": item.provenance_ref,
            "collected_at": item.collected_at,
            "availability": item.availability.value,
            "metadata": dict(item.metadata),
        }
    except AttributeError as exc:
        raise SerializationFailureError(f"EvidenceItem could not be serialized: {exc}") from exc


def from_payload(payload: Dict[str, Any]) -> EvidenceItem:
    schema_version = payload.get("schema_version")
    if schema_version not in _KNOWN_SCHEMA_VERSIONS:
        raise UnsupportedVersionError(
            f"Unsupported EvidenceItem schema_version: {schema_version!r}."
        )

    try:
        return EvidenceItem(
            evidence_id=payload["evidence_id"],
            evidence_type=payload["evidence_type"],
            provenance_ref=payload["provenance_ref"],
            collected_at=payload["collected_at"],
            availability=EvidenceAvailability(payload["availability"]),
            metadata=payload.get("metadata", {}),
        )
    except (KeyError, ValueError, TypeError) as exc:
        raise SerializationFailureError(f"EvidenceItem payload malformed: {exc}") from exc


__all__ = [
    "EVIDENCE_SCHEMA_VERSION",
    "to_payload",
    "from_payload",
]
