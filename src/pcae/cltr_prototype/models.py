"""Prototype-local data model for the Canonical Lifecycle Transition Record.

Translates CLTR-001 v1.0 §6.2 and the 135D formal state-machine model into
concrete, immutable (frozen dataclass) types. Nothing here performs I/O or
validation logic beyond structurally-required-field construction checks
(``ValueError`` on a structurally impossible construction) — semantic
validation lives in ``identity.py``, ``state_machine.py``, and
``invariants.py``.

No production JSON Schema is frozen here (135E §5 explicitly defers this).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


SCHEMA_VERSION = "cltr-prototype-0.1"
CONTRACT_VERSION = "CLTR-001/1.0"


class SpineState(str, Enum):
    """The 12 spine states of the CLTR lifecycle (135D §3.3, §4)."""

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


class OrthogonalFlag(str, Enum):
    """The 2 orthogonal states (135D §3.3) — flags, not spine positions.

    A record can be, e.g., simultaneously TERMINAL_SUCCESS on the spine and
    flagged SUPERSEDED (135D §4's QUARANTINED/SUPERSEDED rows).
    """

    QUARANTINED = "QUARANTINED"
    SUPERSEDED = "SUPERSEDED"


#: All 14 states named by 135D §3.3 (12 spine + 2 orthogonal), for reporting
#: and completeness-checking purposes only. `SpineState` is the type actually
#: carried by `TransitionRecord.spine_state`; orthogonal flags are separate
#: boolean-valued fields (`quarantined`, `superseded`) per 135D's own modeling.
ALL_LIFECYCLE_STATE_NAMES = tuple(s.value for s in SpineState) + tuple(f.value for f in OrthogonalFlag)

TERMINAL_SPINE_STATES = frozenset(
    {
        SpineState.TERMINAL_SUCCESS,
        SpineState.TERMINAL_PARTIAL_EXTERNAL,
        SpineState.FAILED_PRE_CERT,
        SpineState.FAILED_POST_CERT,
    }
)


class TransitionType(str, Enum):
    """The 16 permitted transitions T1-T16 (135D §5)."""

    PROPOSE_TRANSITION = "T1_propose_transition"
    BEGIN_CERTIFICATION = "T2_begin_certification"
    CERTIFY = "T3_certify"
    CERTIFICATION_FAIL = "T4_certification_fail"
    BEGIN_PROMOTION = "T5_begin_promotion"
    PROMOTE_SUCCEED = "T6_promote_succeed"
    PROMOTE_FAIL = "T7_promote_fail"
    BEGIN_NOTIFICATION = "T8_begin_notification"
    NOTIFY_CONFIRM = "T9_notify_confirm"
    NOTIFY_UNCONFIRMED = "T10_notify_unconfirmed"
    NOTIFY_RETRY = "T11_notify_retry"
    RECONCILE_RECEIPT = "T12_reconcile_receipt"
    CLOSE_SUCCESS = "T13_close_success"
    CLOSE_PARTIAL = "T14_close_partial"
    QUARANTINE = "T15_quarantine"
    SUPERSEDE = "T16_supersede"


class TransitionOutcome(str, Enum):
    """Result of attempting to apply a transition function."""

    APPLIED = "applied"
    NOOP_IDEMPOTENT = "noop_idempotent"
    REJECTED_FORBIDDEN = "rejected_forbidden"
    REJECTED_PRECONDITION = "rejected_precondition"


class RetryClassification(str, Enum):
    """Per-state retry/resume classification (135D §24)."""

    BEGIN = "begin"
    CONTINUE = "continue"
    RESUME_AFTER_OBSERVATION = "resume_after_observation"
    RETURN_PRIOR_RESULT = "return_prior_result"
    REPAIR_DERIVATIVE_ONLY = "repair_derivative_only"
    REQUIRE_HUMAN_REVIEW = "require_human_review"
    REJECT_SUPERSEDED_REDIRECT = "reject_superseded_redirect"


class TerminalClassification(str, Enum):
    NOT_TERMINAL = "not_terminal"
    TERMINAL = "terminal"


class ConformanceClassification(str, Enum):
    """135E §23 — a dimension separate from `lifecycle_state`."""

    CONFORMANT = "conformant"
    CONFORMANT_WITH_LEGACY_ADAPTER = "conformant_with_legacy_adapter"
    INCOMPLETE = "incomplete"
    CONFLICTING = "conflicting"
    UNVERIFIABLE = "unverifiable"
    QUARANTINED = "quarantined"
    SUPERSEDED = "superseded"


class AuthorityRole(str, Enum):
    """CLTR-001 §3.1 S/R/D/E/V authority-role model (135E §11)."""

    SOLE = "S"
    REFERENCE = "R"
    DERIVATIVE = "D"
    IMMUTABLE_EVENT = "E"
    VERIFICATION_ONLY = "V"


class CommitOwnershipClassification(str, Enum):
    """The frozen three-outcome model (CLTR-001 §10.4, 135E §12.1)."""

    VERIFIED = "verified"
    CONTAMINATED = "contaminated"
    UNVERIFIABLE = "unverifiable"


class CommitRole(str, Enum):
    """135E §12 item 14 — declared commit role, never inferred from message text."""

    SOURCE_CHANGE = "source_change"
    DOCUMENTATION = "documentation"
    REPAIR = "repair"
    VERIFICATION_ONLY = "verification_only"


class InvariantResultOutcome(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    INAPPLICABLE = "inapplicable"


class EvidenceType(str, Enum):
    TEST_SUITE_RESULT = "test_suite_result"
    GOVERNANCE_CHECK_RESULT = "governance_check_result"
    REPORT = "report"
    METADATA = "metadata"
    RUNTIME_SNAPSHOT = "runtime_snapshot"
    NARRATIVE_ONLY = "narrative_only"


class EvidenceVerificationStatus(str, Enum):
    BOUND = "bound"
    UNAVAILABLE = "unavailable"
    STALE = "stale"
    UNAVAILABLE_STRUCTURED = "unavailable_structured"


class RepresentationKind(str, Enum):
    """The 15 cross-representation comparison targets (135D §9 rows 2-16)."""

    CANONICAL_REPORT = "canonical_report"
    COMPLETION_METADATA = "completion_metadata"
    ARCHITECTURE_STATUS = "architecture_status"
    IMMUTABLE_SNAPSHOT = "immutable_snapshot"
    CHECKPOINT = "checkpoint"
    PROMOTED_REPORT = "promoted_report"
    PROMOTED_METADATA = "promoted_metadata"
    MUTABLE_LATEST_POINTER = "mutable_latest_pointer"
    NOTIFICATION_PAYLOAD = "notification_payload"
    NOTIFICATION_RESULT = "notification_result"
    COMPLETION_MARKER = "completion_marker"
    FINALIZATION_RECEIPT = "finalization_receipt"
    GIT_ATTRIBUTION_VIEW = "git_attribution_view"
    REPOSITORY_TRANSITION_VIEW = "repository_transition_view"
    TERMINAL_REPOSITORY_STATE_OBSERVATIONS = "terminal_repository_state_observations"


class ComparisonFieldClassification(str, Enum):
    """135E §14 — per-field comparison classification."""

    EXACT_MATCH = "exact_match"
    DIGEST_BOUND_MATCH = "digest_bound_match"
    DERIVED_MATCH = "derived_match"
    PRESENTATION_ONLY = "presentation_only"
    TOLERATED_LEGACY_ABSENCE = "tolerated_legacy_absence"
    CONFLICT = "conflict"
    UNVERIFIABLE_CONDITION = "unverifiable_condition"


class FailureClassification(str, Enum):
    """135D §27 failure-state architecture."""

    NONE = "none"
    MISSING_AUTHORITY = "missing_authority"
    IDENTITY_CONFLICT = "identity_conflict"
    COMMIT_OWNERSHIP_CONFLICT = "commit_ownership_conflict"
    PROJECTION_CONFLICT = "projection_conflict"
    SEMANTIC_MISMATCH = "semantic_mismatch"
    CERTIFICATION_FAILURE = "certification_failure"
    CHECKPOINT_FAILURE = "checkpoint_failure"
    PROMOTION_FAILURE = "promotion_failure"
    ATOMIC_POINTER_FAILURE = "atomic_pointer_failure"
    NOTIFICATION_FAILURE = "notification_failure"
    NOTIFICATION_UNCERTAINTY = "notification_uncertainty"
    MARKER_FAILURE = "marker_failure"
    RECEIPT_FAILURE = "receipt_failure"
    DIGEST_FAILURE = "digest_failure"
    STALE_DERIVATIVE = "stale_derivative"
    CROSS_PHASE_SUBSTITUTION = "cross_phase_substitution"
    REPOSITORY_FINAL_STATE_MISMATCH = "repository_final_state_mismatch"
    COMPATIBILITY_ADAPTER_FAILURE = "compatibility_adapter_failure"


class CompatibilityConfidence(str, Enum):
    """135E §21 item 9 — identity-source disclosure for compatibility adapters."""

    EXPLICIT_DECLARED = "explicit_declared"
    NARRATIVE_PARSED_COMPARISON_ONLY = "narrative_parsed_comparison_only"


@dataclass(frozen=True)
class Identity:
    transition_id: str
    phase_id: str
    repository_identity: str
    branch_identity: str
    task_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.transition_id:
            raise ValueError("Identity.transition_id is required and must be non-empty")
        if not self.phase_id:
            raise ValueError("Identity.phase_id is required and must be non-empty")
        if not self.repository_identity:
            raise ValueError("Identity.repository_identity is required and must be non-empty")
        if not self.branch_identity:
            raise ValueError("Identity.branch_identity is required and must be non-empty")


@dataclass(frozen=True)
class EvidenceRef:
    """A reference to evidence — never a copy of its content (R/E-role, 135E §13)."""

    evidence_id: str
    evidence_type: EvidenceType
    transition_id: str
    phase_id: str
    verification_status: EvidenceVerificationStatus
    source_path: Optional[str] = None
    digest: Optional[str] = None
    source_revision: Optional[str] = None
    observation_timestamp: Optional[str] = None
    limitation: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.evidence_id:
            raise ValueError("EvidenceRef.evidence_id is required")
        if not self.transition_id:
            raise ValueError("EvidenceRef.transition_id is required")
        if not self.phase_id:
            raise ValueError("EvidenceRef.phase_id is required")


@dataclass(frozen=True)
class CommitDeclaration:
    """An explicitly declared commit hash plus its declared role (135E §12)."""

    commit_hash: str
    declared_role: CommitRole

    def __post_init__(self) -> None:
        if not self.commit_hash:
            raise ValueError("CommitDeclaration.commit_hash is required")


@dataclass(frozen=True)
class CommitClassificationResult:
    """The evaluated three-outcome classification for one declared commit."""

    commit_hash: str
    classification: CommitOwnershipClassification
    reason: str


@dataclass(frozen=True)
class TransitionRecord:
    """The prototype-local Canonical Lifecycle Transition Record.

    Immutable value object. A transition function never mutates a record in
    place; it produces a new `TransitionRecord` value (135E §9's return model).
    """

    identity: Identity
    spine_state: SpineState
    source_revision: str

    schema_version: str = SCHEMA_VERSION
    contract_version: str = CONTRACT_VERSION

    final_revision: Optional[str] = None
    final_revision_provisional: bool = True

    prior_state: Optional[SpineState] = None
    projected_state: Optional[dict] = None
    certified_state: Optional[dict] = None

    quarantined: bool = False
    superseded: bool = False
    superseded_by: Optional[str] = None

    declared_commits: tuple[CommitDeclaration, ...] = field(default_factory=tuple)
    commit_classifications: tuple[CommitClassificationResult, ...] = field(default_factory=tuple)

    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)

    report_binding: Optional[EvidenceRef] = None
    metadata_binding: Optional[EvidenceRef] = None
    snapshot_binding: Optional[EvidenceRef] = None
    checkpoint_binding: Optional[EvidenceRef] = None
    promotion_binding: Optional[EvidenceRef] = None
    notification_binding: Optional[EvidenceRef] = None
    marker_binding: Optional[EvidenceRef] = None
    receipt_binding: Optional[EvidenceRef] = None
    architecture_status_binding: Optional[EvidenceRef] = None

    timestamps: dict = field(default_factory=dict)

    failure_classification: FailureClassification = FailureClassification.NONE
    limitations: tuple[str, ...] = field(default_factory=tuple)
    compatibility_metadata: dict = field(default_factory=dict)

    record_digest: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.source_revision:
            raise ValueError("TransitionRecord.source_revision is required")
        if self.spine_state == SpineState.CERTIFIED and self.certified_state is None:
            # CERTIFIED-or-later must carry a certified_state (135E §5).
            raise ValueError("TransitionRecord: certified_state is required from CERTIFIED onward")

    def with_updates(self, **kwargs) -> "TransitionRecord":
        """Produce a new immutable record value with the given fields replaced."""
        import dataclasses

        return dataclasses.replace(self, **kwargs)

    @property
    def is_terminal(self) -> bool:
        return self.spine_state in TERMINAL_SPINE_STATES

    @property
    def terminal_classification(self) -> TerminalClassification:
        return TerminalClassification.TERMINAL if self.is_terminal else TerminalClassification.NOT_TERMINAL
