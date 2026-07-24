"""Deterministic serialization framework for ``Session`` records (Phase
143K), extended in Phase 143M with sibling serializers for
``EvidenceItem``, ``Clarification``, and ``AuditEvent``. Each artifact
class's serializer is exposed under its own name (``evidence_to_payload``/
``evidence_from_payload``, etc.) rather than a single overloaded
``to_payload``/``from_payload`` pair, so a caller's import makes explicit
which artifact class it is serializing -- no Preview Digest, confirmation,
publication, or CHGR serializer exists here, since this package
implements none of those artifacts.
"""

from __future__ import annotations

from pcae.interactive_workflow.serialization import audit_schema as _audit_schema
from pcae.interactive_workflow.serialization import (
    clarification_schema as _clarification_schema,
)
from pcae.interactive_workflow.serialization import evidence_schema as _evidence_schema
from pcae.interactive_workflow.serialization.schema import (
    SCHEMA_VERSION,
    from_payload,
    to_payload,
)

evidence_to_payload = _evidence_schema.to_payload
evidence_from_payload = _evidence_schema.from_payload
clarification_to_payload = _clarification_schema.to_payload
clarification_from_payload = _clarification_schema.from_payload
audit_to_payload = _audit_schema.to_payload
audit_from_payload = _audit_schema.from_payload

__all__ = [
    "SCHEMA_VERSION",
    "from_payload",
    "to_payload",
    "evidence_to_payload",
    "evidence_from_payload",
    "clarification_to_payload",
    "clarification_from_payload",
    "audit_to_payload",
    "audit_from_payload",
]
