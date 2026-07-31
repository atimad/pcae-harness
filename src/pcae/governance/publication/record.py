"""CHGR record construction (Phase 144C; widened Phase 144F, Phase 146G;
PEC-001 §7, §9, §10, §20; CHGR-001 §8, §9, §10, §26, CHGR-REQ-194 through
CHGR-REQ-209).

Builds the four schema-conformant CHGR-001 v1.2 artifacts one Publication
Execution produces -- ``human_governance_record``,
``human_confirmation_evidence``, ``governance_record_provenance``,
``governance_record_integrity`` -- and fail-closed validates the complete
set against the frozen ``src/pcae/schema_resources/chgr`` schema family
before returning, refusing (``ChgrSchemaConformanceError``, no partial
result) if any artifact does not validate (CHGR-REQ-204, CHGR-REQ-205).
Every field is computed solely from the ``PublicationReadinessPackage``
the Coordinator was handed -- its only substantive input (PEC-001
"Coordinator Inputs"); ``event`` (the Publication Authorization Event) is
accepted for call-site signature stability but contributes no field to
any CHGR-001 schema-shaped artifact, none of which models an
authorization event (that is the Coordinator's own audit trail,
``PublicationRecordStore.record_attempt``).

**Construction order (146F §3.3, Risk R-1):** ``human_confirmation_evidence``
first (no forward reference), then ``governance_record_provenance``
(cites the confirmation evidence), then a genuine forward-reference cycle
between ``human_governance_record.integrity_ref`` and
``governance_record_integrity.payload_digest`` -- CHGR-REQ-203 requires
``payload_digest`` to be the top-level record's *real, final* digest,
which can only be known once ``human_governance_record`` is fully
finalized, but ``human_governance_record.integrity_ref`` must itself
already cite ``governance_record_integrity``'s own digest to be complete.
Resolved by computing a *provisional* ``governance_record_integrity``
digest (real content, placeholder ``payload_digest``) to seed
``integrity_ref``, finalizing ``human_governance_record`` for real, then
finalizing ``governance_record_integrity`` for real with the true
``payload_digest``. Per ``shared/references.schema.json``'s own
documented discipline, an ``artifact_reference``'s ``record_digest`` is
shape-checked only -- whether it matches the referenced artifact's real
digest is an explicitly out-of-scope, verification-layer responsibility
-- so ``integrity_ref`` citing the provisional (pre-patch) digest is
schema-conformant, not a defect; disclosed in
``human_governance_record.limitations`` below.

**``authority_basis_claimed`` (CHGR-001 §10/§11, updated Phase 147M):** a
claim citing the bound Decision Template's own ``eligible_authority`` text
(CHGR-REQ-096). Populated, citation-only and verbatim (AESIC-001 v1.3
§14/§22, AESIC-REQ-058), from ``package.citation_text`` whenever the
package carries a paired ``authority_evaluation_ref``/``citation_text`` --
i.e. whenever an upstream Authority Evaluation Service Stage 2 evaluation
ran before ``PublicationHandoff.build_package`` was called. When neither
is present (no Authority Evaluation Service configured upstream, the
ordinary case for any caller predating Phase 147M), this field remains
unpopulated, per PEC-REQ-115's explicit "never from an independent
judgment" discipline: inventing a citation the package does not carry
would itself be a prohibited inference. Its absence is disclosed in
``human_governance_record.limitations`` (CHGR-REQ-199, CHGR-REQ-208).
"""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any, Dict, Mapping

from pcae.governance.publication.chgr_envelope import (
    chgr_timestamp,
    envelope_for,
    validate_chgr_artifact,
)
from pcae.governance.publication.chgr_rendering import render_human_governance_record
from pcae.governance.publication.errors import ChgrSchemaConformanceError
from pcae.governance.publication.models import PublicationAuthorizationEvent
from pcae.interactive_workflow.publication_handoff.models import PublicationReadinessPackage

_ASSURANCE_LEVEL_BY_EVIDENCE_KIND = {
    "typed_confirmation_only": "L0",
    "os_authenticated_user": "L1",
}

_RECORD_ID_PREFIX_BY_FAMILY = {
    "human_governance_record": "chgr",
    "human_confirmation_evidence": "chgrconf",
    "governance_record_provenance": "chgrprov",
    "governance_record_integrity": "chgrintg",
}

_PLACEHOLDER_DIGEST = "0" * 64


def _new_record_id(record_family: str) -> str:
    return f"{_RECORD_ID_PREFIX_BY_FAMILY[record_family]}-{uuid.uuid4().hex}"


def _artifact_reference(record_id: str, record_digest: str, record_family: str) -> Dict[str, str]:
    return {"record_id": record_id, "record_digest": record_digest, "record_family": record_family}


def _normalize_identity_evidence(evidence: Mapping[str, Any]) -> Dict[str, Any]:
    normalized = dict(evidence)
    captured_at = normalized.get("captured_at")
    if isinstance(captured_at, str):
        normalized["captured_at"] = chgr_timestamp(captured_at)
    return normalized


def _assurance_level_for(evidence_kind: Any) -> str:
    try:
        return _ASSURANCE_LEVEL_BY_EVIDENCE_KIND[evidence_kind]
    except KeyError:
        raise ChgrSchemaConformanceError(
            f"decision_maker_identity_evidence.evidence_kind {evidence_kind!r} has no known "
            "assurance-level mapping (only 'typed_confirmation_only' -> L0 and "
            "'os_authenticated_user' -> L1 are supported this increment, CHGR-REQ-200); "
            "refusing construction rather than guessing."
        ) from None


def _authority_basis_disclosure_present(record: Dict[str, Any]) -> bool:
    if "authority_basis_claimed" not in record:
        return any("authority_basis_claimed" in entry for entry in record.get("limitations", []))
    return True


def _validate_chgr_bundle(bundle: Dict[str, Dict[str, Any]]) -> None:
    """CHGR-REQ-204/205's fail-closed gate: every artifact must validate
    against its own schema, and CHGR-REQ-208's disclosure check (not
    expressible in JSON Schema alone) must hold, additive to, never a
    substitute for, schema validation (146F §4.2, §4.7)."""

    issues: list[str] = []
    for family, artifact in bundle.items():
        result = validate_chgr_artifact(artifact)
        if not result.ok:
            issues.extend(
                f"{family}: {issue.code} at {issue.instance_path!r}: {issue.message}"
                for issue in result.issues
            )
    if not _authority_basis_disclosure_present(bundle["human_governance_record"]):
        issues.append(
            "human_governance_record: authority_basis_claimed is absent but no limitations "
            "entry names its absence (CHGR-REQ-199, CHGR-REQ-208)."
        )
    if issues:
        raise ChgrSchemaConformanceError(
            "Publication refused: constructed CHGR artifact set does not validate "
            "(CHGR-REQ-204, CHGR-REQ-205): " + "; ".join(issues)
        )


def build_publication_record(
    package: PublicationReadinessPackage,
    event: PublicationAuthorizationEvent,
    record_id: str,
    created_at: str,
) -> Dict[str, Dict[str, Any]]:
    """Build and fail-closed-validate the four CHGR-001 v1.2 artifacts for
    one Publication Execution. Pure function of ``package``/``record_id``/
    ``created_at``; never reads or mutates any other state.

    Returns a four-key bundle: ``human_governance_record``,
    ``human_confirmation_evidence``, ``governance_record_provenance``,
    ``governance_record_integrity``. Raises ``ChgrSchemaConformanceError``
    -- and constructs nothing durable -- if the set does not validate.
    """
    del event  # accepted for signature stability only; see module docstring.

    confirmer_identity = _normalize_identity_evidence(package.decision_maker_identity_evidence)
    achieved_assurance_level = _assurance_level_for(confirmer_identity.get("evidence_kind"))

    # -- 1. human_confirmation_evidence: no forward reference -----------
    id1 = _new_record_id("human_confirmation_evidence")
    body1: Dict[str, Any] = {
        **envelope_for("human_confirmation_evidence", id1, created_at),
        "confirmed_content_digest": package.preview_digest,
        "preview_rendering_digest": package.preview_digest,
        "confirmation_statement": package.confirmation_statement,
        "confirmation_timestamp": chgr_timestamp(package.confirmation_timestamp),
        "confirmer_identity_evidence": confirmer_identity,
        "achieved_assurance_level": achieved_assurance_level,
        "limitations": [],
        "extensions": {},
    }
    body1["record_digest"] = compute_record_digest(body1)

    # -- 2. governance_record_provenance: cites artifact 1 --------------
    id2 = _new_record_id("governance_record_provenance")
    body2: Dict[str, Any] = {
        **envelope_for("governance_record_provenance", id2, created_at),
        "template_used_ref": {"template_id": package.template_id, "version": package.template_version},
        "options_presented": list(package.options_presented),
        "selected_option_id": package.selected_option_id,
        "preview_content_digest": package.preview_digest,
        "confirmation_event_ref": _artifact_reference(
            id1, body1["record_digest"], "human_confirmation_evidence"
        ),
        "repository_provenance": {"available": False},
        "limitations": [
            "repository_provenance.available is false: this construction path is a pure "
            "function of the PublicationReadinessPackage/PublicationAuthorizationEvent only, "
            "with no repository or git read (CHGR-REQ-202).",
        ],
        "extensions": {},
    }
    if package.rationale_text is not None:
        body2["rationale_given"] = package.rationale_text
    body2["record_digest"] = compute_record_digest(body2)

    # -- 3/4. human_governance_record + governance_record_integrity -----
    id3 = record_id
    id4 = _new_record_id("governance_record_integrity")

    rendering_digest = hashlib.sha256(
        render_human_governance_record(
            {
                "decision_subject": package.decision_subject,
                "template_ref": {"template_id": package.template_id, "version": package.template_version},
                "selected_option_id": package.selected_option_id,
                "decision_maker_identity_evidence": confirmer_identity,
                "rationale": package.rationale_text,
                "conditions": package.conditions_text,
                "assurance_level": achieved_assurance_level,
                "lifecycle_state": "published",
            }
        ).encode("utf-8")
    ).hexdigest()

    integrity_envelope = envelope_for("governance_record_integrity", id4, created_at)
    provisional_body4 = {
        **integrity_envelope,
        "payload_digest": _PLACEHOLDER_DIGEST,
        "rendering_digest": rendering_digest,
        "digest_algorithm": "sha256",
        "limitations": [],
        "extensions": {},
    }
    provisional_digest4 = compute_record_digest(provisional_body4)

    body3: Dict[str, Any] = {
        **envelope_for("human_governance_record", id3, created_at),
        "decision_subject": package.decision_subject,
        "template_ref": {"template_id": package.template_id, "version": package.template_version},
        "selected_option_id": package.selected_option_id,
        "decision_maker_identity_evidence": confirmer_identity,
        "assurance_level": achieved_assurance_level,
        "lifecycle_state": "published",
        "confirmation_evidence_ref": _artifact_reference(
            id1, body1["record_digest"], "human_confirmation_evidence"
        ),
        "provenance_ref": _artifact_reference(id2, body2["record_digest"], "governance_record_provenance"),
        "integrity_ref": _artifact_reference(id4, provisional_digest4, "governance_record_integrity"),
        "limitations": [
            "integrity_ref.record_digest cites governance_record_integrity's provisional digest "
            "(computed before that artifact's own payload_digest was finalized, to resolve the "
            "146F Sec.3.3 forward-reference cycle between this field and "
            "governance_record_integrity.payload_digest); whether it matches the persisted "
            "artifact's actual record_digest is a verification-layer responsibility, never a "
            "schema-layer guarantee (shared/references.schema.json).",
        ],
        "extensions": {},
    }
    # AESIC-001 v1.3 §14/§22, AESIC-REQ-058: only the Authority Evaluation
    # Record's own citation_text ever flows into authority_basis_claimed,
    # verbatim, citation-only -- never the AER itself, never
    # evaluation_result, never declaration_ref. Absent an
    # authority_evaluation_ref/citation_text pair on the package (the
    # ordinary case when no Authority Evaluation Service is configured
    # upstream), this field remains unpopulated and disclosed, unchanged
    # from this record's own pre-AESIC-001 behavior.
    if package.authority_evaluation_ref is not None and package.citation_text:
        body3["authority_basis_claimed"] = package.citation_text
    else:
        body3["limitations"].insert(
            0,
            "authority_basis_claimed is not populated: no Authority Evaluation Service "
            "citation was supplied on this PublicationReadinessPackage "
            "(authority_evaluation_ref/citation_text both absent) (CHGR-REQ-199, "
            "CHGR-REQ-207, CHGR-REQ-208; PEC-REQ-115 names this field's construction as a "
            "MAY, contingent on that citation resolving, never a requirement or an "
            "invention this record may perform in its absence).",
        )
    if package.rationale_text is not None:
        body3["rationale"] = package.rationale_text
    if package.conditions_text is not None:
        body3["conditions"] = package.conditions_text
    body3["record_digest"] = compute_record_digest(body3)

    body4: Dict[str, Any] = {
        **integrity_envelope,
        "payload_digest": body3["record_digest"],
        "rendering_digest": rendering_digest,
        "digest_algorithm": "sha256",
        "limitations": [],
        "extensions": {},
    }
    body4["record_digest"] = compute_record_digest(body4)

    bundle = {
        "human_governance_record": body3,
        "human_confirmation_evidence": body1,
        "governance_record_provenance": body2,
        "governance_record_integrity": body4,
    }
    _validate_chgr_bundle(bundle)
    return bundle


def compute_record_digest(body: Dict[str, Any]) -> str:
    """Deterministic SHA-256 hex digest of ``body`` with any pre-existing
    ``record_digest`` key excluded, mirroring
    ``src/pcae/schema_resources/chgr/shared/digest.schema.json``'s bare
    64-character lowercase hex convention."""

    payload = {key: value for key, value in body.items() if key != "record_digest"}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


__all__ = ["build_publication_record", "compute_record_digest"]
