"""Stage 2 candidate-artifact derivation (135Q §9-§16).

Every candidate is derived from the same shared transition-input package
(and the CLTR record already derived from it) Stage 1 already built --
never independently re-assembled, never read from mutable production
files after the fact. Every candidate carries an explicit
``non_authority_disclosure`` and ``artifact_role`` field; none may claim
to be a production artifact (135Q §8).
"""

from __future__ import annotations

from pcae.cltr.migration.cltr_derivation import CltrDerivationResult
from pcae.cltr.migration.disclosure import NON_AUTHORITY_DISCLOSURE
from pcae.cltr.migration.legacy_derivation import LegacyDerivationResult
from pcae.cltr.migration.rehearsal.enums import ArtifactRole, CandidateKind, VerificationStatus
from pcae.cltr.migration.rehearsal.models import CandidateArtifact
from pcae.cltr.migration.shared_input import SharedTransitionInputPackage

#: 135Q §15 -- a rehearsal marker candidate must never use a bare
#: production state literal (``pcae phase-report reconcile`` prints the
#: literal ``already_dispatched`` today).
_MARKER_STATE = "rehearsal_candidate_dispatched_simulated"

#: 135Q §16 -- a rehearsal receipt candidate must never use the literal
#: production terminal-state value (``pcae phase-report reconcile``
#: prints the literal ``finalized`` today).
_RECEIPT_STATE = "rehearsal_recorded"


def _base(rehearsal_generation_id: str, transition_id: str) -> dict:
    return {
        "rehearsal_generation_id": rehearsal_generation_id,
        "transition_id": transition_id,
        "non_authority_disclosure": dict(NON_AUTHORITY_DISCLOSURE),
    }


def build_cltr_record_candidate(
    *, rehearsal_generation_id: str, package: SharedTransitionInputPackage, cltr: CltrDerivationResult
) -> CandidateArtifact:
    content = _base(rehearsal_generation_id, package.transition_id)
    unverifiable = cltr.status != "constructed" or cltr.record is None
    content.update(
        {
            "status": cltr.status,
            "record_digest": cltr.record_digest,
            "phase_id": package.phase_id,
            "limitations": list(cltr.limitations),
        }
    )
    return CandidateArtifact(
        kind=CandidateKind.CLTR_RECORD,
        artifact_role=ArtifactRole.UNVERIFIABLE if unverifiable else ArtifactRole.CLTR_DERIVED,
        verification_status=VerificationStatus.UNVERIFIABLE if unverifiable else VerificationStatus.VERIFIED,
        content=content,
    )


def build_report_candidate(
    *, rehearsal_generation_id: str, package: SharedTransitionInputPackage, legacy: LegacyDerivationResult
) -> CandidateArtifact:
    content = _base(rehearsal_generation_id, package.transition_id)
    report_id = legacy.fields.get("report_id")
    content.update(
        {
            "report_role": "rehearsal_candidate",
            # 135Q §10 -- the candidate's own report_id is a rehearsal-
            # scoped identity, never equal to the authoritative report_id.
            "report_id": f"rehearsal:{rehearsal_generation_id}:{report_id or 'unresolved'}",
            "phase_id": package.phase_id,
            "report_digest": legacy.fields.get("report_digest"),
            "test_results": {"fast_green": package.field("fast_green_summary")},
        }
    )
    unverifiable = legacy.fields.get("report_digest") is None
    return CandidateArtifact(
        kind=CandidateKind.REPORT_CANDIDATE,
        artifact_role=ArtifactRole.UNVERIFIABLE if unverifiable else ArtifactRole.CLTR_DERIVED,
        verification_status=VerificationStatus.UNVERIFIABLE if unverifiable else VerificationStatus.VERIFIED,
        content=content,
    )


def build_metadata_candidate(
    *, rehearsal_generation_id: str, package: SharedTransitionInputPackage, legacy: LegacyDerivationResult
) -> CandidateArtifact:
    content = _base(rehearsal_generation_id, package.transition_id)
    content.update(
        {
            "phase_id": package.phase_id,
            "metadata_id": f"rehearsal:{rehearsal_generation_id}:metadata",
            "report_digest_binding": legacy.fields.get("report_digest"),
            "notification_delivery_timestamp": {
                "value": None,
                "reason": "external_effect_not_occurred",
            },
        }
    )
    return CandidateArtifact(
        kind=CandidateKind.METADATA_CANDIDATE,
        artifact_role=ArtifactRole.CLTR_DERIVED,
        verification_status=VerificationStatus.VERIFIED,
        content=content,
    )


def build_architecture_status_candidate(
    *, rehearsal_generation_id: str, package: SharedTransitionInputPackage, runtime_snapshot: dict
) -> CandidateArtifact:
    content = _base(rehearsal_generation_id, package.transition_id)
    transition_type = package.field("transition_type")
    content.update(
        {
            "phase_id": package.phase_id,
            "transition_status": package.field("lifecycle_state"),
            "no_active_phase_after_completion": bool(transition_type),
            # 135Q §12 -- never parsed from prose; explicitly null when the
            # shared input never bound a successor.
            "recommended_next_phase": package.field("recommended_next_phase"),
            "runtime_state": dict(runtime_snapshot),
            "limitations": ["successor phase is advisory, not binding"],
        }
    )
    return CandidateArtifact(
        kind=CandidateKind.ARCHITECTURE_STATUS_CANDIDATE,
        artifact_role=ArtifactRole.PROJECTED,
        verification_status=VerificationStatus.VERIFIED,
        content=content,
    )


def build_checkpoint_candidate(
    *, rehearsal_generation_id: str, package: SharedTransitionInputPackage, state: str
) -> CandidateArtifact:
    content = _base(rehearsal_generation_id, package.transition_id)
    content.update({"phase_id": package.phase_id, "state": state})
    return CandidateArtifact(
        kind=CandidateKind.CHECKPOINT_CANDIDATE,
        artifact_role=ArtifactRole.CLTR_DERIVED,
        verification_status=VerificationStatus.VERIFIED,
        content=content,
    )


def build_notification_intent_candidate(
    *, rehearsal_generation_id: str, package: SharedTransitionInputPackage, report_digest: str | None
) -> CandidateArtifact:
    content = _base(rehearsal_generation_id, package.transition_id)
    content.update(
        {
            "notification_id": f"rehearsal:{rehearsal_generation_id}:notification",
            "phase_id": package.phase_id,
            "report_digest": report_digest,
            # 135Q §14 -- channel type only, never a credential/address.
            "intended_channel": "telegram",
            # 135Q §14 -- namespaced so it can never collide with a real
            # production PFN-001 idempotency key.
            "idempotency_key": f"rehearsal:{rehearsal_generation_id}:{package.transition_id}",
            "delivery_attempted": False,
            "rehearsal_only_status": True,
        }
    )
    return CandidateArtifact(
        kind=CandidateKind.NOTIFICATION_INTENT_CANDIDATE,
        artifact_role=ArtifactRole.EXTERNAL_EFFECT_INTENT,
        verification_status=VerificationStatus.VERIFIED,
        content=content,
    )


def build_marker_candidate(
    *, rehearsal_generation_id: str, package: SharedTransitionInputPackage, notification_id: str, report_digest: str | None
) -> CandidateArtifact:
    content = _base(rehearsal_generation_id, package.transition_id)
    content.update(
        {
            "marker_candidate_id": f"rehearsal:{rehearsal_generation_id}:marker",
            "report_digest_binding": report_digest,
            "notification_intent_binding": notification_id,
            "state": _MARKER_STATE,
            "uncertainty_semantics": "NOTIFIED_UNCONFIRMED",
        }
    )
    return CandidateArtifact(
        kind=CandidateKind.MARKER_CANDIDATE,
        artifact_role=ArtifactRole.EXTERNAL_EFFECT_INTENT,
        verification_status=VerificationStatus.VERIFIED,
        content=content,
    )


def build_receipt_candidate(
    *, rehearsal_generation_id: str, package: SharedTransitionInputPackage, marker_id: str, notification_id: str
) -> CandidateArtifact:
    content = _base(rehearsal_generation_id, package.transition_id)
    content.update(
        {
            "delivery_confirmed": False,
            "production_completion_authority": "legacy",
            "receipt_role": "rehearsal_candidate",
            "marker_candidate_binding": marker_id,
            "notification_intent_candidate_binding": notification_id,
            "state": _RECEIPT_STATE,
            "delivery_timestamp": {"value": None, "reason": "rehearsal_no_external_effect"},
        }
    )
    return CandidateArtifact(
        kind=CandidateKind.RECEIPT_CANDIDATE,
        artifact_role=ArtifactRole.EXTERNAL_EFFECT_INTENT,
        verification_status=VerificationStatus.VERIFIED,
        content=content,
    )


def build_commit_attribution_candidate(
    *, rehearsal_generation_id: str, package: SharedTransitionInputPackage, cltr: CltrDerivationResult
) -> CandidateArtifact:
    """135Q §9 item 9 -- exercises the F-135P-3 fix: a non-empty
    ``phase_commit_ownership`` no longer crashes derivation."""

    content = _base(rehearsal_generation_id, package.transition_id)
    entries = []
    unverifiable = cltr.record is None
    if cltr.record is not None:
        entries = [
            {
                "commit_hash": e.commit_hash,
                "certification_state": e.certification_state.value,
                "repository_identity": e.repository_identity,
                "branch_identity": e.branch_identity,
            }
            for e in cltr.record.phase_commit_ownership
        ]
    content.update({"phase_commit_ownership": entries})
    return CandidateArtifact(
        kind=CandidateKind.COMMIT_ATTRIBUTION_CANDIDATE,
        artifact_role=ArtifactRole.UNVERIFIABLE if unverifiable else ArtifactRole.CLTR_DERIVED,
        verification_status=VerificationStatus.UNVERIFIABLE if unverifiable else VerificationStatus.VERIFIED,
        content=content,
    )


def build_repository_transition_candidate(
    *, rehearsal_generation_id: str, package: SharedTransitionInputPackage
) -> CandidateArtifact:
    content = _base(rehearsal_generation_id, package.transition_id)
    content.update(
        {
            "phase_id": package.phase_id,
            "entry_point": package.entry_point,
            "predecessor_transition_id": package.predecessor_transition_id,
            "migration_epoch": package.migration_epoch,
            "authority_epoch": package.authority_epoch,
        }
    )
    return CandidateArtifact(
        kind=CandidateKind.REPOSITORY_TRANSITION_CANDIDATE,
        artifact_role=ArtifactRole.PROJECTED,
        verification_status=VerificationStatus.VERIFIED,
        content=content,
    )
