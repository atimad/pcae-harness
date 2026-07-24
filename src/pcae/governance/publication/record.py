"""CHGR record construction (Phase 144C; PEC-001 §7, §9, §10; CHGR-001
§8, §9, §10).

Builds the deterministic, self-contained JSON payload the Publication
Coordinator's atomic write persists: canonical identity assignment
(CHGR-001 §9) and provenance/integrity capture (CHGR-001 §10), both
computed solely from the ``PublicationReadinessPackage`` and
``PublicationAuthorizationEvent`` the Coordinator was handed -- its only
two permitted inputs (PEC-001 "Coordinator Inputs").

**Documented scope limitation** (see Phase 144C's report §15 for the full
discussion): this record's ``package_reference`` section carries
identifier/digest references only, exactly as
``PublicationReadinessPackage`` itself does (IWC-001 v1.1 §11.4, Phase
143O) -- never a payload copy. CHGR-001 §10's Provenance Contract also
calls for verbatim decision content (selected option, decision-maker
identity, the exact preview content confirmed, decision subject,
authority basis claimed) that ``PublicationReadinessPackage`` does not
carry, by IWC-001's own deliberate reference-only design, and that PEC-
001's Integration section forbids the Coordinator from separately
fetching (no coupling to ``SessionCoordinator``, ``PreviewBuilder``,
``ConfirmationController``, etc.). This record therefore is not, and does
not claim to be, schema-validatable against
``pcae.schema_resources.chgr.records.human_governance_record.schema.json``
-- doing so would require inventing field values PEC-001's own boundary
does not make available to this Coordinator, which PEC-REQ-109 names as
"evidence of a defect requiring a governed contract revision, never
license to informally resolve it in code." This record fully satisfies
PEC-001's own literal text: an atomic write, a stable canonical identity,
and provenance/integrity evidence "sufficient" to reconstruct which
package and which Authorization Event were consumed, deferring full
CHGR-001 §10 verbatim-content capture to a future, separately governed
phase.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict

from pcae.governance.publication.models import PublicationAuthorizationEvent
from pcae.interactive_workflow.publication_handoff.models import PublicationReadinessPackage

CHGR_RECORD_SCHEMA_VERSION = "governance-publication-coordinator-chgr-record/0.1"

_KNOWN_LIMITATIONS = (
    "package_reference carries identifier/digest references only, not verbatim "
    "decision content (CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md Sec.10's "
    "selected_option_id, decision_subject, decision_maker_identity_evidence, "
    "authority_basis_claimed, and verbatim preview content are not reconstructable "
    "from PublicationReadinessPackage alone under PUBLICATION_EXECUTION_CONTRACT.md's "
    "own Integration boundary). Resolving this gap requires a future, separately "
    "governed contract revision (PEC-REQ-109), not this record's own invention.",
)


def build_publication_record(
    package: PublicationReadinessPackage,
    event: PublicationAuthorizationEvent,
    record_id: str,
    created_at: str,
) -> Dict[str, Any]:
    """Build the deterministic CHGR record payload for one Publication
    Execution. Pure function of its three arguments plus ``record_id``/
    ``created_at``; never reads or mutates any other state."""

    body: Dict[str, Any] = {
        "record_schema_version": CHGR_RECORD_SCHEMA_VERSION,
        "record_id": record_id,
        "record_type": "publication_coordinator_chgr",
        "created_at": created_at,
        "package_reference": {
            "package_id": package.package_id,
            "session_id": package.session_id,
            "session_state": package.session_state.value,
            "transition_sequence_number": package.transition_sequence_number,
            "preview_id": package.preview_id,
            "preview_digest": package.preview_digest,
            "confirmation_request_id": package.confirmation_request_id,
            "confirmation_response_id": package.confirmation_response_id,
            "evidence_refs": list(package.evidence_refs),
            "clarification_refs": list(package.clarification_refs),
            "audit_refs": list(package.audit_refs),
            "built_at": package.built_at,
            "package_schema_version": package.schema_version,
        },
        "publication_authorization": {
            "event_id": event.event_id,
            "operator_id": event.operator_id,
            "package_id": event.package_id,
            "invoked_at": event.invoked_at,
        },
        "limitations": list(_KNOWN_LIMITATIONS),
    }
    body["record_digest"] = compute_record_digest(body)
    return body


def compute_record_digest(body: Dict[str, Any]) -> str:
    """Deterministic SHA-256 hex digest of ``body`` with any pre-existing
    ``record_digest`` key excluded, mirroring
    ``src/pcae/schema_resources/chgr/shared/digest.schema.json``'s bare
    64-character lowercase hex convention."""

    payload = {key: value for key, value in body.items() if key != "record_digest"}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


__all__ = ["CHGR_RECORD_SCHEMA_VERSION", "build_publication_record", "compute_record_digest"]
