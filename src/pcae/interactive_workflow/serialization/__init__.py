"""Deterministic serialization framework for ``Session`` records (Phase
143K), extended in Phase 143M with sibling serializers for
``EvidenceItem``, ``Clarification``, and ``AuditEvent``, in Phase 143N
with sibling serializers for ``Preview``, ``ConfirmationRequest``, and
``ConfirmationResponse``, and in Phase 143O with a sibling serializer for
``PublicationReadinessPackage``. Each artifact class's serializer is
exposed under its own name (``evidence_to_payload``/
``evidence_from_payload``, etc.) rather than a single overloaded
``to_payload``/``from_payload`` pair, so a caller's import makes explicit
which artifact class it is serializing -- no publication-result or CHGR
serializer exists here, since this package implements neither artifact
(``publication_handoff_schema`` serializes only the readiness *package*'s
own structural references, never a publication outcome).
"""

from __future__ import annotations

from pcae.interactive_workflow.serialization import audit_schema as _audit_schema
from pcae.interactive_workflow.serialization import (
    clarification_schema as _clarification_schema,
)
from pcae.interactive_workflow.serialization import (
    confirmation_schema as _confirmation_schema,
)
from pcae.interactive_workflow.serialization import evidence_schema as _evidence_schema
from pcae.interactive_workflow.serialization import preview_schema as _preview_schema
from pcae.interactive_workflow.serialization import (
    publication_handoff_schema as _publication_handoff_schema,
)
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
preview_to_payload = _preview_schema.to_payload
preview_from_payload = _preview_schema.from_payload
confirmation_request_to_payload = _confirmation_schema.request_to_payload
confirmation_request_from_payload = _confirmation_schema.request_from_payload
confirmation_response_to_payload = _confirmation_schema.response_to_payload
confirmation_response_from_payload = _confirmation_schema.response_from_payload
publication_handoff_to_payload = _publication_handoff_schema.to_payload
publication_handoff_from_payload = _publication_handoff_schema.from_payload

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
    "preview_to_payload",
    "preview_from_payload",
    "confirmation_request_to_payload",
    "confirmation_request_from_payload",
    "confirmation_response_to_payload",
    "confirmation_response_from_payload",
    "publication_handoff_to_payload",
    "publication_handoff_from_payload",
]
