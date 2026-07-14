"""Stage 2 rehearsal wire enums (135Q §8/§9/§13/§22/§26/§27/§30)."""

from __future__ import annotations

from enum import Enum


class CandidateKind(str, Enum):
    """The file-producing subset of 135Q §9's 23-item candidate inventory
    (items 1-10), matching 135Q §7's own example directory listing
    exactly. Items 11-14 (git-attribution view, compatibility/legacy
    view, diagnostic envelope, reconciliation view) are disclosed,
    non-blocking, non-stored views per 135S's own scoping decision (see
    ``docs/PHASE_135_ATOMIC_PUBLICATION_REHEARSAL_IMPLEMENTATION.md``);
    items 15-23 (shared-input/Stage-1-evidence references, comparison
    results, manifest, digests, epochs, limitations, disclosure) are
    bound directly into the manifest (135Q §18) rather than emitted as
    separate files."""

    CLTR_RECORD = "cltr_record"
    REPORT_CANDIDATE = "report_candidate"
    METADATA_CANDIDATE = "metadata_candidate"
    ARCHITECTURE_STATUS_CANDIDATE = "architecture_status_candidate"
    CHECKPOINT_CANDIDATE = "checkpoint_candidate"
    NOTIFICATION_INTENT_CANDIDATE = "notification_intent_candidate"
    MARKER_CANDIDATE = "marker_candidate"
    RECEIPT_CANDIDATE = "receipt_candidate"
    COMMIT_ATTRIBUTION_CANDIDATE = "commit_attribution_candidate"
    REPOSITORY_TRANSITION_CANDIDATE = "repository_transition_candidate"


#: Fixed digest order for candidate artifacts (135Q §19 "canonical
#: artifact ordering") -- never directory-listing order.
CANDIDATE_ORDER: tuple[CandidateKind, ...] = tuple(CandidateKind)

#: Record-bearing/derivative kinds (135Q §9 items 1-9): an unverifiable
#: artifact of one of these kinds blocks rehearsal pointer publication
#: (135Q §22). ``REPOSITORY_TRANSITION_CANDIDATE`` is the sole
#: observational (V-role) kind and does not block.
CRITICAL_KINDS = frozenset(
    {
        CandidateKind.CLTR_RECORD,
        CandidateKind.REPORT_CANDIDATE,
        CandidateKind.METADATA_CANDIDATE,
        CandidateKind.ARCHITECTURE_STATUS_CANDIDATE,
        CandidateKind.CHECKPOINT_CANDIDATE,
        CandidateKind.NOTIFICATION_INTENT_CANDIDATE,
        CandidateKind.MARKER_CANDIDATE,
        CandidateKind.RECEIPT_CANDIDATE,
        CandidateKind.COMMIT_ATTRIBUTION_CANDIDATE,
    }
)

#: Kinds whose comparison against the authoritative artifact may contain
#: fields dependent on an external effect Stage 2 never attempts (135Q
#: §31) -- classified as expected differences, never fabricated matches.
EXPECTED_DIFFERENCE_KINDS = frozenset(
    {
        CandidateKind.NOTIFICATION_INTENT_CANDIDATE,
        CandidateKind.MARKER_CANDIDATE,
        CandidateKind.RECEIPT_CANDIDATE,
    }
)


class ArtifactRole(str, Enum):
    """135Q §8's seven-role vocabulary. Never ``production_authoritative``
    -- no rehearsal artifact may claim that role."""

    COPIED_EVIDENCE = "copied_evidence"
    NORMALIZED_LEGACY = "normalized_legacy"
    CLTR_DERIVED = "cltr_derived"
    EXTERNAL_EFFECT_INTENT = "external_effect_intent"
    UNVERIFIABLE = "unverifiable"
    PROJECTED = "projected"


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    UNVERIFIABLE = "unverifiable"
    QUARANTINED = "quarantined"


class CheckpointState(str, Enum):
    """135Q §13's nine rehearsal-scoped checkpoint states."""

    GENERATION_PREPARATION = "generation_preparation"
    GENERATION_VERIFIED = "generation_verified"
    REHEARSAL_POINTER_UNPUBLISHED = "rehearsal_pointer_unpublished"
    REHEARSAL_POINTER_PUBLICATION_ATTEMPTED = "rehearsal_pointer_publication_attempted"
    REHEARSAL_POINTER_PUBLISHED = "rehearsal_pointer_published"
    COMPARISON_COMPLETED = "comparison_completed"
    REHEARSAL_TERMINAL_STATE = "rehearsal_terminal_state"
    FAILURE = "failure"
    ROLLBACK_REHEARSAL = "rollback_rehearsal"


class RecoveryState(str, Enum):
    """135Q §27's eleven state-based recovery states."""

    NO_CANDIDATE = "no_candidate"
    CANDIDATE_INCOMPLETE = "candidate_incomplete"
    CANDIDATE_COMPLETE_UNVERIFIED = "candidate_complete_unverified"
    CANDIDATE_VERIFIED_NOT_FINALIZED = "candidate_verified_not_finalized"
    GENERATION_FINALIZED_UNPUBLISHED = "generation_finalized_unpublished"
    POINTER_PUBLICATION_UNCERTAIN = "pointer_publication_uncertain"
    POINTER_PUBLISHED = "pointer_published"
    RESULT_RECORD_INCOMPLETE = "result_record_incomplete"
    QUARANTINE_REQUIRED = "quarantine_required"
    ROLLBACK_REHEARSAL_REQUESTED = "rollback_rehearsal_requested"


class RehearsalOutcome(str, Enum):
    """135Q §30's terminal outcomes for one rehearsal attempt."""

    SUCCESSFUL = "successful_rehearsal"
    REJECTED_PRECONDITION = "rejected_precondition"
    BLOCKED_BY_MISMATCH = "blocked_by_mismatch"
    FAILED = "failed_rehearsal"
    UNCERTAIN_PUBLICATION = "uncertain_publication"
    IDEMPOTENT_REPLAY = "idempotent_replay"
    CONFLICT = "conflict"
    QUARANTINED = "quarantined"


class RollbackOutcome(str, Enum):
    """135U -- rollback-rehearsal-specific outcomes (135Q §33's evidence
    shape, applied to a rollback attempt rather than a forward rehearsal
    attempt). Distinct from ``RehearsalOutcome`` because a rollback
    attempt has its own terminal vocabulary (135U phase brief:
    "distinguish rollback requested / rejected / verified / published /
    publication uncertain / idempotent replay / conflicting replay /
    recovery required / reconciled / quarantined")."""

    REQUESTED = "rollback_requested"
    REJECTED = "rollback_rejected"
    VERIFIED = "rollback_verified"
    PUBLISHED = "rollback_published"
    PUBLICATION_UNCERTAIN = "rollback_publication_uncertain"
    IDEMPOTENT_REPLAY = "rollback_idempotent_replay"
    CONFLICT = "rollback_conflict"
    RECOVERY_REQUIRED = "rollback_recovery_required"
    RECONCILED = "rollback_reconciled"
    QUARANTINED = "rollback_quarantined"
