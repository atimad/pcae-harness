"""CHGR record construction (Phase 144C; widened Phase 144F; PEC-001 §7,
§9, §10, §20; CHGR-001 §8, §9, §10).

Builds the deterministic, self-contained JSON payload the Publication
Coordinator's atomic write persists: canonical identity assignment
(CHGR-001 §9) and provenance/integrity capture (CHGR-001 §10), both
computed solely from the ``PublicationReadinessPackage`` and
``PublicationAuthorizationEvent`` the Coordinator was handed -- its only
two permitted inputs (PEC-001 "Coordinator Inputs").

**Phase 144F widening (PEC-001 v1.1 §20, PEC-REQ-111 through
PEC-REQ-117):** ``PublicationReadinessPackage`` now carries, verbatim
(IWC-001 v1.2 §26, IWC-REQ-185), the decision content CHGR-001 §10
requires. This module carries that content, unmodified, into three named
substantive structures -- ``human_governance_record``,
``human_confirmation_evidence``, ``governance_record_provenance`` --
populating exactly the fields PEC-REQ-112 names, directly and only from
the package's own verbatim fields; never independently fetched, computed,
or re-derived (PEC-REQ-113: no new import of ``interactive_workflow``
internals is introduced to do so -- every value below was already an
argument to this function before this widening, sourced from the
package).

**Remaining, disclosed limitation:** ``authority_basis_claimed``
(CHGR-001 §10/§11) is a claim citing the bound Decision Template's own
``eligible_authority`` text (CHGR-REQ-096). No Decision Template model
exists anywhere in this repository carrying an ``eligible_authority``
field (interactive_workflow's ``Session.template_ref`` is an opaque
identifier only), so no such citation is available to construct from.
PEC-REQ-115 states the Coordinator *MAY* construct this field where the
package's template citation resolves to that text -- it does not resolve
here, so this record does not populate ``authority_basis_claimed``, per
PEC-REQ-115's explicit "never from an independent judgment" discipline:
inventing a citation the package does not carry would itself be a
prohibited inference. Full schema-envelope fields for the three named
structures (their own ``schema_id``/``record_id``/``record_digest``,
``assurance_level``, ``lifecycle_state``, cross-artifact reference
digests) are likewise not separately assigned by this record -- CHGR-001
§9's canonical identity assignment for the *top-level* record is already
performed by ``PublicationCoordinator.execute`` (this module's caller);
assigning independent canonical identities to these three sub-structures
as fully separate, schema-validated CHGR artifacts is a distinct
undertaking this phase's own scope (widen the Package, populate its
content into the Coordinator's record) does not authorize.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict

from pcae.governance.publication.models import PublicationAuthorizationEvent
from pcae.interactive_workflow.publication_handoff.models import PublicationReadinessPackage

CHGR_RECORD_SCHEMA_VERSION = "governance-publication-coordinator-chgr-record/0.1"

_KNOWN_LIMITATIONS = (
    "authority_basis_claimed is not populated: no Decision Template "
    "eligible_authority citation is available anywhere in this repository's "
    "interactive_workflow models to construct it from (PEC-REQ-115 names this "
    "field's construction as a MAY, contingent on that citation resolving, never "
    "a requirement or an invention this record may perform in its absence).",
    "human_governance_record/human_confirmation_evidence/governance_record_provenance "
    "above carry substantive CHGR-001 Sec.10 content only, populated verbatim from "
    "PublicationReadinessPackage (PEC-REQ-112); full schema-envelope fields for "
    "these three structures as independently schema-validated CHGR artifacts "
    "(their own record_id/record_digest/assurance_level/lifecycle_state/"
    "cross-artifact reference digests) are not separately assigned here -- out of "
    "this record's own scope.",
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
        "human_governance_record": {
            "decision_subject": package.decision_subject,
            "template_ref": {
                "template_id": package.template_id,
                "version": package.template_version,
            },
            "selected_option_id": package.selected_option_id,
            "decision_maker_identity_evidence": dict(package.decision_maker_identity_evidence),
            "rationale": package.rationale_text,
            "conditions": package.conditions_text,
        },
        "human_confirmation_evidence": {
            "confirmation_statement": package.confirmation_statement,
            "confirmation_timestamp": package.confirmation_timestamp,
            "confirmer_identity_evidence": dict(package.decision_maker_identity_evidence),
            "preview_rendering_digest": package.preview_digest,
        },
        "governance_record_provenance": {
            "template_used_ref": {
                "template_id": package.template_id,
                "version": package.template_version,
            },
            "options_presented": list(package.options_presented),
            "selected_option_id": package.selected_option_id,
            "rationale_given": package.rationale_text,
            "preview_content_digest": package.preview_digest,
            "preview_rendered_content": package.preview_rendered_content,
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
