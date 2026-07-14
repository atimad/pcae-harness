"""Production CLTR enumerations — exact wire values frozen by
CLTR-SCHEMA-001 v1.0.1 (Phase 135I §3, §9, 135J §21.4).

Every value here is copied verbatim from the frozen contract text. This
module introduces no new lifecycle semantics and renames nothing for
convenience (phase brief, "Exact lifecycle inventory").
"""

from __future__ import annotations

from enum import Enum


class LifecycleState(str, Enum):
    """135I §3.1 — 12 spine values. QUARANTINED/SUPERSEDED are never carried
    here; they are overlay flags (`OverlayFlag`, §3.1)."""

    PROPOSED = "PROPOSED"
    CERTIFYING = "CERTIFYING"
    CERTIFIED = "CERTIFIED"
    PROMOTING = "PROMOTING"
    PROMOTED = "PROMOTED"
    NOTIFYING = "NOTIFYING"
    NOTIFIED = "NOTIFIED"
    NOTIFIED_UNCONFIRMED = "NOTIFIED_UNCONFIRMED"
    TERMINAL_SUCCESS = "TERMINAL_SUCCESS"
    TERMINAL_PARTIAL_EXTERNAL = "TERMINAL_PARTIAL_EXTERNAL"
    FAILED_PRE_CERT = "FAILED_PRE_CERT"
    FAILED_POST_CERT = "FAILED_POST_CERT"


#: All 14 lifecycle-state names (12 spine + 2 orthogonal overlay), per the
#: phase brief's "exact 14 states" inventory requirement.
class OverlayFlag(str, Enum):
    QUARANTINED = "QUARANTINED"
    SUPERSEDED = "SUPERSEDED"


ALL_LIFECYCLE_STATE_NAMES = tuple(s.value for s in LifecycleState) + tuple(f.value for f in OverlayFlag)
assert len(ALL_LIFECYCLE_STATE_NAMES) == 14

SPINE_TERMINAL_STATES = frozenset(
    {
        LifecycleState.TERMINAL_SUCCESS,
        LifecycleState.TERMINAL_PARTIAL_EXTERNAL,
        LifecycleState.FAILED_PRE_CERT,
        LifecycleState.FAILED_POST_CERT,
    }
)

#: 135I §6.3 — every CERTIFIED-or-later state must carry certified content.
CERTIFIED_OR_LATER_STATES = frozenset(
    {
        LifecycleState.CERTIFIED,
        LifecycleState.PROMOTING,
        LifecycleState.PROMOTED,
        LifecycleState.NOTIFYING,
        LifecycleState.NOTIFIED,
        LifecycleState.NOTIFIED_UNCONFIRMED,
        LifecycleState.TERMINAL_SUCCESS,
        LifecycleState.TERMINAL_PARTIAL_EXTERNAL,
        LifecycleState.FAILED_POST_CERT,
    }
)


class TransitionType(str, Enum):
    """135I §3.2 — 16 transitions T1-T16."""

    PROPOSE_TRANSITION = "propose_transition"
    BEGIN_CERTIFICATION = "begin_certification"
    CERTIFY = "certify"
    CERTIFICATION_FAIL = "certification_fail"
    BEGIN_PROMOTION = "begin_promotion"
    PROMOTE_SUCCEED = "promote_succeed"
    PROMOTE_FAIL = "promote_fail"
    BEGIN_NOTIFICATION = "begin_notification"
    NOTIFY_CONFIRM = "notify_confirm"
    NOTIFY_UNCONFIRMED = "notify_unconfirmed"
    NOTIFY_RETRY = "notify_retry"
    RECONCILE_RECEIPT = "reconcile_receipt"
    CLOSE_SUCCESS = "close_success"
    CLOSE_PARTIAL = "close_partial"
    QUARANTINE = "quarantine"
    SUPERSEDE = "supersede"


assert len(list(TransitionType)) == 16

#: 135I §3.5 — permitted-next-state lookup table, restated as data. Maps
#: (from_state, transition_type) -> resulting LifecycleState. Orthogonal
#: transitions (quarantine/supersede) map to the *same* lifecycle_state
#: (they only ever change overlay_flags) and are validated separately.
PERMITTED_TRANSITIONS: dict[tuple[LifecycleState, TransitionType], LifecycleState] = {
    (LifecycleState.PROPOSED, TransitionType.BEGIN_CERTIFICATION): LifecycleState.CERTIFYING,
    (LifecycleState.CERTIFYING, TransitionType.CERTIFY): LifecycleState.CERTIFIED,
    (LifecycleState.CERTIFYING, TransitionType.CERTIFICATION_FAIL): LifecycleState.FAILED_PRE_CERT,
    (LifecycleState.CERTIFIED, TransitionType.BEGIN_PROMOTION): LifecycleState.PROMOTING,
    (LifecycleState.PROMOTING, TransitionType.PROMOTE_SUCCEED): LifecycleState.PROMOTED,
    (LifecycleState.PROMOTING, TransitionType.PROMOTE_FAIL): LifecycleState.FAILED_POST_CERT,
    (LifecycleState.PROMOTED, TransitionType.BEGIN_NOTIFICATION): LifecycleState.NOTIFYING,
    (LifecycleState.NOTIFYING, TransitionType.NOTIFY_CONFIRM): LifecycleState.NOTIFIED,
    (LifecycleState.NOTIFYING, TransitionType.NOTIFY_UNCONFIRMED): LifecycleState.NOTIFIED_UNCONFIRMED,
    (LifecycleState.NOTIFYING, TransitionType.NOTIFY_RETRY): LifecycleState.NOTIFYING,
    (LifecycleState.NOTIFIED, TransitionType.CLOSE_SUCCESS): LifecycleState.TERMINAL_SUCCESS,
    (LifecycleState.NOTIFIED_UNCONFIRMED, TransitionType.NOTIFY_CONFIRM): LifecycleState.NOTIFIED,
    (LifecycleState.NOTIFIED_UNCONFIRMED, TransitionType.CLOSE_PARTIAL): LifecycleState.TERMINAL_PARTIAL_EXTERNAL,
}

#: The two orthogonal transitions apply to any CERTIFIED-or-later state and
#: never change lifecycle_state (135I §3.2, §3.5 last row).
ORTHOGONAL_TRANSITIONS = frozenset({TransitionType.QUARANTINE, TransitionType.SUPERSEDE})

#: 135I §3.3 / 135D §6 — the 14 forbidden transitions are the complement of
#: PERMITTED_TRANSITIONS over the full (state, transition) product, per
#: state. This constant enumerates them explicitly so completeness can be
#: tested (phase brief, "exact 14 forbidden transitions").
FORBIDDEN_TRANSITIONS: tuple[tuple[LifecycleState, TransitionType], ...] = (
    (LifecycleState.PROPOSED, TransitionType.CERTIFY),
    (LifecycleState.PROPOSED, TransitionType.PROMOTE_SUCCEED),
    (LifecycleState.CERTIFYING, TransitionType.BEGIN_PROMOTION),
    (LifecycleState.CERTIFIED, TransitionType.CERTIFY),
    (LifecycleState.CERTIFIED, TransitionType.PROMOTE_SUCCEED),
    (LifecycleState.PROMOTING, TransitionType.BEGIN_NOTIFICATION),
    (LifecycleState.PROMOTED, TransitionType.NOTIFY_CONFIRM),
    (LifecycleState.NOTIFYING, TransitionType.CLOSE_SUCCESS),
    (LifecycleState.NOTIFIED, TransitionType.NOTIFY_CONFIRM),
    (LifecycleState.NOTIFIED, TransitionType.CLOSE_PARTIAL),
    (LifecycleState.NOTIFIED_UNCONFIRMED, TransitionType.CLOSE_SUCCESS),
    (LifecycleState.TERMINAL_SUCCESS, TransitionType.BEGIN_CERTIFICATION),
    (LifecycleState.FAILED_PRE_CERT, TransitionType.BEGIN_CERTIFICATION),
    (LifecycleState.FAILED_POST_CERT, TransitionType.BEGIN_PROMOTION),
)
assert len(FORBIDDEN_TRANSITIONS) == 14
assert set(FORBIDDEN_TRANSITIONS).isdisjoint(set(PERMITTED_TRANSITIONS))


class AuthorityRole(str, Enum):
    """CLTR-001 §3.1, 135I §4.2 — S/R/D/E/V."""

    SOLE = "S"
    REFERENCE = "R"
    DERIVATIVE = "D"
    IMMUTABLE_EVIDENCE = "E"
    VERIFICATION_ONLY = "V"


class RepresentationKind(str, Enum):
    """135I §5, §9 — the 15 representation kinds."""

    CANONICAL_REPORT = "canonical_report"
    COMPLETION_METADATA = "completion_metadata"
    ARCHITECTURE_STATUS = "architecture_status"
    IMMUTABLE_SNAPSHOT = "immutable_snapshot"
    CHECKPOINT = "checkpoint"
    PROMOTED_REPORT = "promoted_report"
    PROMOTED_METADATA = "promoted_metadata"
    NOTIFICATION_PAYLOAD = "notification_payload"
    MARKER = "marker"
    RECEIPT = "receipt"
    REPOSITORY_TRANSITION_VIEW = "repository_transition_view"
    GIT_ATTRIBUTION_VIEW = "git_attribution_view"
    COMPATIBILITY_VIEW = "compatibility_view"
    DIAGNOSTIC_ENVELOPE = "diagnostic_envelope"
    RECONCILIATION_VIEW = "reconciliation_view"


assert len(list(RepresentationKind)) == 15


class AdapterComparisonMode(str, Enum):
    """135I §21.1 — five-value taxonomy."""

    EXACT_IDENTITY_DIGEST = "exact_identity_digest"
    NORMALIZED_SEMANTIC = "normalized_semantic"
    OBSERVATIONAL = "observational"
    PRESENTATION_ONLY = "presentation_only"
    UNSUPPORTED = "unsupported"


#: 135J §21.4 — per-kind comparison-mode assignment (the repair that bumped
#: the schema from 1.0.0 to 1.0.1). No kind is `unsupported`.
REPRESENTATION_COMPARISON_MODE: dict[RepresentationKind, AdapterComparisonMode] = {
    RepresentationKind.CANONICAL_REPORT: AdapterComparisonMode.EXACT_IDENTITY_DIGEST,
    RepresentationKind.COMPLETION_METADATA: AdapterComparisonMode.EXACT_IDENTITY_DIGEST,
    RepresentationKind.ARCHITECTURE_STATUS: AdapterComparisonMode.NORMALIZED_SEMANTIC,
    RepresentationKind.IMMUTABLE_SNAPSHOT: AdapterComparisonMode.EXACT_IDENTITY_DIGEST,
    RepresentationKind.CHECKPOINT: AdapterComparisonMode.NORMALIZED_SEMANTIC,
    RepresentationKind.PROMOTED_REPORT: AdapterComparisonMode.EXACT_IDENTITY_DIGEST,
    RepresentationKind.PROMOTED_METADATA: AdapterComparisonMode.EXACT_IDENTITY_DIGEST,
    RepresentationKind.NOTIFICATION_PAYLOAD: AdapterComparisonMode.NORMALIZED_SEMANTIC,
    RepresentationKind.MARKER: AdapterComparisonMode.NORMALIZED_SEMANTIC,
    RepresentationKind.RECEIPT: AdapterComparisonMode.NORMALIZED_SEMANTIC,
    RepresentationKind.REPOSITORY_TRANSITION_VIEW: AdapterComparisonMode.OBSERVATIONAL,
    RepresentationKind.GIT_ATTRIBUTION_VIEW: AdapterComparisonMode.OBSERVATIONAL,
    RepresentationKind.COMPATIBILITY_VIEW: AdapterComparisonMode.NORMALIZED_SEMANTIC,
    RepresentationKind.DIAGNOSTIC_ENVELOPE: AdapterComparisonMode.PRESENTATION_ONLY,
    RepresentationKind.RECONCILIATION_VIEW: AdapterComparisonMode.OBSERVATIONAL,
}
assert set(REPRESENTATION_COMPARISON_MODE) == set(RepresentationKind)


class ConformanceState(str, Enum):
    """135I §22.1 / 135G §17 — 7 values."""

    CONFORMANT = "conformant"
    CONFORMANT_WITH_LEGACY_ADAPTER = "conformant_with_legacy_adapter"
    INCOMPLETE = "incomplete"
    CONFLICTING = "conflicting"
    UNVERIFIABLE = "unverifiable"
    QUARANTINED = "quarantined"
    SUPERSEDED = "superseded"


class ComparisonOutcome(str, Enum):
    """135K comparison-result classes (phase brief §22): distinguish
    conformant / partially conformant / incompatible / unverifiable."""

    CONFORMANT = "conformant"
    PARTIALLY_CONFORMANT = "partially_conformant"
    INCOMPATIBLE = "incompatible"
    UNVERIFIABLE = "unverifiable"


class CertificationState(str, Enum):
    """CLTR-001 §10.4, 135I §9 — three-outcome commit classification."""

    VERIFIED = "verified"
    CONTAMINATED = "contaminated"
    UNVERIFIABLE = "unverifiable"


class CommitRelationshipClassification(str, Enum):
    """135I §9 — capability-only enum."""

    OWN_SOURCE_CHANGE = "own_source_change"
    OWN_DOCUMENTATION_ONLY = "own_documentation_only"
    OWN_REPAIR = "own_repair"
    OWN_VERIFICATION_ONLY = "own_verification_only"
    OWN_FINALIZATION_COMMIT = "own_finalization_commit"
    UNCLASSIFIED = "unclassified"


class RetryClassification(str, Enum):
    RETRYABLE_FROM_SCRATCH = "retryable_from_scratch"
    RETRYABLE_VIA_NEW_RECORD = "retryable_via_new_record"
    NOT_RETRYABLE_TERMINAL = "not_retryable_terminal"
    NOT_RETRYABLE_IN_PROGRESS = "not_retryable_in_progress"
    RETRYABLE_RECONCILIATION_ONLY = "retryable_reconciliation_only"


class RecoveryClassification(str, Enum):
    NONE_REQUIRED = "none_required"
    RESUME_SAFE = "resume_safe"
    OBSERVE_REQUIRED = "observe_required"
    RECONCILIATION_REQUIRED = "reconciliation_required"


class TerminalClassification(str, Enum):
    NON_TERMINAL = "non_terminal"
    TERMINAL = "terminal"
    TERMINAL_PARTIAL = "terminal_partial"


def derive_terminal_classification(state: LifecycleState) -> TerminalClassification:
    if state == LifecycleState.TERMINAL_SUCCESS:
        return TerminalClassification.TERMINAL
    if state == LifecycleState.TERMINAL_PARTIAL_EXTERNAL:
        return TerminalClassification.TERMINAL_PARTIAL
    if state in (LifecycleState.FAILED_PRE_CERT, LifecycleState.FAILED_POST_CERT):
        return TerminalClassification.TERMINAL
    return TerminalClassification.NON_TERMINAL


def derive_retry_classification(state: LifecycleState) -> RetryClassification:
    if state in (LifecycleState.PROPOSED, LifecycleState.FAILED_PRE_CERT):
        return RetryClassification.RETRYABLE_FROM_SCRATCH
    if state == LifecycleState.FAILED_POST_CERT:
        return RetryClassification.RETRYABLE_VIA_NEW_RECORD
    if state in (LifecycleState.TERMINAL_SUCCESS, LifecycleState.TERMINAL_PARTIAL_EXTERNAL):
        return RetryClassification.NOT_RETRYABLE_TERMINAL
    if state in (LifecycleState.CERTIFYING, LifecycleState.PROMOTING, LifecycleState.NOTIFYING):
        return RetryClassification.NOT_RETRYABLE_IN_PROGRESS
    if state == LifecycleState.NOTIFIED_UNCONFIRMED:
        return RetryClassification.RETRYABLE_RECONCILIATION_ONLY
    return RetryClassification.NOT_RETRYABLE_IN_PROGRESS


def derive_recovery_classification(state: LifecycleState) -> RecoveryClassification:
    if state == LifecycleState.CERTIFIED:
        return RecoveryClassification.RESUME_SAFE
    if state in (LifecycleState.PROMOTING, LifecycleState.NOTIFYING):
        return RecoveryClassification.OBSERVE_REQUIRED
    if state == LifecycleState.NOTIFIED_UNCONFIRMED:
        return RecoveryClassification.RECONCILIATION_REQUIRED
    return RecoveryClassification.NONE_REQUIRED


class FailureClassification(str, Enum):
    """135I §9 — 17 values, CLTR-001 §18."""

    IDENTITY_RESOLUTION_FAILURE = "identity_resolution_failure"
    COMMIT_OWNERSHIP_CONFLICT = "commit_ownership_conflict"
    SEMANTIC_MISMATCH = "semantic_mismatch"
    EVIDENCE_UNAVAILABLE = "evidence_unavailable"
    CERTIFICATION_CHECK_FAILURE = "certification_check_failure"
    SNAPSHOT_SEAL_FAILURE = "snapshot_seal_failure"
    PROMOTION_DISPATCH_FAILURE = "promotion_dispatch_failure"
    PROMOTION_OUTCOME_UNCONFIRMED = "promotion_outcome_unconfirmed"
    NOTIFICATION_DISPATCH_FAILURE = "notification_dispatch_failure"
    NOTIFICATION_OUTCOME_UNCONFIRMED = "notification_outcome_unconfirmed"
    RECEIPT_MODELING_FAILURE = "receipt_modeling_failure"
    ATOMIC_VISIBILITY_FAILURE = "atomic_visibility_failure"
    DUPLICATE_CONFLICTING_REPLAY = "duplicate_conflicting_replay"
    CROSS_PHASE_REPLAY = "cross_phase_replay"
    STALE_POINTER_DETECTED = "stale_pointer_detected"
    QUARANTINE_INTEGRITY_FAILURE = "quarantine_integrity_failure"
    REPOSITORY_STATE_MISMATCH = "repository_state_mismatch"


assert len(list(FailureClassification)) == 17


class NotificationState(str, Enum):
    NOT_ATTEMPTED = "not_attempted"
    ATTEMPTING = "attempting"
    CONFIRMED = "confirmed"
    UNCONFIRMED = "unconfirmed"
    FAILED = "failed"


class ReconciliationOutcome(str, Enum):
    """135I §18.3, adopted from 135H.2 §7."""

    RECONCILED = "reconciled"
    DELIVERY_RECORDED_BOOKKEEPING_INCOMPLETE = "delivery_recorded_bookkeeping_incomplete"
    PROMOTION_OUTCOME_UNCONFIRMED = "promotion_outcome_unconfirmed"
    NOT_DELIVERED = "not_delivered"
    CONFLICT = "conflict"


class InvariantResult(str, Enum):
    """135I §12.2 — three values only."""

    PASS = "pass"
    FAIL = "fail"
    INAPPLICABLE = "inapplicable"


#: 135I §12.1, 135D §11, independently re-confirmed by 135J §12 — the
#: normative 37-ID crosswalk. (invariant_id, category, one-line assertion).
INVARIANT_CATALOG: tuple[tuple[str, str, str], ...] = (
    ("CLTR-ID-1", "identity", "All representations of a transition share exactly one transition_id"),
    ("CLTR-ID-2", "identity", "All representations of a phase's most recent transition share exactly one phase_id"),
    ("CLTR-AUTH-1", "authority", "A lifecycle fact has exactly one authoritative source within a transition"),
    ("CLTR-AUTH-2", "authority", "No derivative independently reconstructs a fact the record does not carry"),
    ("CLTR-STATE-1", "state", "A completed phase never appears in any derivative's active classification"),
    ("CLTR-STATE-2", "state", "A planned successor is never classified active until CERTIFIED or later"),
    ("CLTR-STATE-3", "state", "No state transitions backward along the spine"),
    ("CLTR-STATE-4", "state", "No state skips a required predecessor"),
    ("CLTR-ORDER-1", "ordering", "No checkpoint before certification"),
    ("CLTR-ORDER-2", "ordering", "No promotion before checkpoint"),
    ("CLTR-ORDER-3", "ordering", "No terminal notification before promotion"),
    ("CLTR-ORDER-4", "ordering", "No irreversible stage precedes semantic certification"),
    ("CLTR-ORDER-5", "ordering", "No post-certification mutable read may redefine the transition"),
    ("CLTR-ORDER-6", "ordering", "No marker before required delivery classification"),
    ("CLTR-ORDER-7", "ordering", "No receipt may claim completion before actual stage completion"),
    ("CLTR-DERIVE-1", "derivation", "Every derivative is a pure function of the record plus referenced evidence"),
    ("CLTR-DERIVE-2", "derivation", "Regeneration of any derivative from the same sealed record is byte-identical"),
    ("CLTR-COMMIT-1", "commit", "Declared phase commits equal the commits any derivative report claims as phase-owned"),
    ("CLTR-COMMIT-2", "commit", "Every declared commit resolves to exactly one of verified/contaminated/unverifiable"),
    ("CLTR-COMMIT-3", "commit", "Fabricated hashes are never silently equivalent to verified"),
    ("CLTR-EVID-1", "evidence", "Report prose never serves as sole evidence for an R/E-role fact"),
    ("CLTR-PERSIST-1", "persistence", "The current pointer never exposes a mixed-generation report/metadata pair"),
    ("CLTR-PERSIST-2", "persistence", "Immutable history is never rewritten"),
    ("CLTR-PERSIST-3", "persistence", "The mutable current pointer is always reconstructible from immutable history"),
    ("CLTR-RETRY-1", "retry", "NOTIFIED_UNCONFIRMED is resume-terminal by the record's own logic, not only entry points"),
    ("CLTR-RETRY-2", "retry", "A duplicate ordinary completion for an already-terminal phase/task is rejected"),
    ("CLTR-RETRY-3", "retry", "Recovery from an unknown-outcome crash always observes actual external state before deciding"),
    ("CLTR-NOTIFY-1", "notify", "Notification references promoted canonical evidence, never independently re-gathered evidence"),
    ("CLTR-NOTIFY-2", "notify", "Notification retry only from NOTIFYING, never from NOTIFIED/NOTIFIED_UNCONFIRMED"),
    ("CLTR-MARKER-1", "marker", "Marker and receipt for a transition bind the same transition_id"),
    ("CLTR-MARKER-2", "marker", "Marker presence alone is never sufficient proof of terminal state"),
    ("CLTR-RECEIPT-1", "receipt", "Receipt reflects actual observed delivery outcome, never assumed/optimistic"),
    ("CLTR-COMPAT-1", "compat", "Historical artifacts are never rewritten, migrated in place, or reinterpreted as record-produced"),
    ("CLTR-COMPAT-2", "compat", "PFN-001 and PFR-001 remain unamended by any CLTR-001-conformant work"),
    ("CLTR-SAFE-1", "safety", "Runtime remains Observed/observe/execution unavailable throughout any CLTR-001-conformant work"),
    ("CLTR-SAFE-2", "safety", "The record never becomes an execution-authorization mechanism"),
    ("CLTR-SAFE-3", "safety", "Terminal states are recognized consistently by the record's own core logic and every consuming entry point"),
)
assert len(INVARIANT_CATALOG) == 37
assert len({row[0] for row in INVARIANT_CATALOG}) == 37

INVARIANT_IDS: tuple[str, ...] = tuple(row[0] for row in INVARIANT_CATALOG)

#: 135I §12.2 — all 37 are Blocking (field exists for schema extensibility).
BLOCKING_INVARIANT_IDS = frozenset(INVARIANT_IDS)
