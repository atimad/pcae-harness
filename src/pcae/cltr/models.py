"""Typed production CLTR record model (135I §7) and the explicit shadow
transition input contract (phase 135K brief, "Explicit input object").

Deeply immutable value objects: nested dict/list values are frozen via
``_deep_freeze`` so a caller cannot mutate a constructed record's nested
structures after the fact (phase brief: "Do not rely on shallow frozen
dataclasses if nested mutation remains possible").
"""

from __future__ import annotations

import dataclasses
from types import MappingProxyType
from typing import Optional

from pcae.cltr import schema
from pcae.cltr.enums import (
    AuthorityRole,
    CertificationState,
    CommitRelationshipClassification,
    FailureClassification,
    LifecycleState,
    NotificationState,
    RecoveryClassification,
    RetryClassification,
    TerminalClassification,
    TransitionType,
    derive_recovery_classification,
    derive_retry_classification,
    derive_terminal_classification,
)


def _deep_freeze(value):
    if isinstance(value, dict):
        return MappingProxyType({k: _deep_freeze(v) for k, v in sorted(value.items())})
    if isinstance(value, (list, tuple)):
        return tuple(_deep_freeze(v) for v in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_deep_freeze(v) for v in value)
    return value


@dataclasses.dataclass(frozen=True)
class CommitOwnershipEntry:
    """135I §10.1 — one entry in `phase_commit_ownership`."""

    commit_hash: str
    repository_identity: str
    branch_identity: str
    certification_state: CertificationState
    commit_relationship: CommitRelationshipClassification = CommitRelationshipClassification.UNCLASSIFIED
    contamination_evidence: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.commit_hash:
            raise ValueError("CommitOwnershipEntry.commit_hash is required")


@dataclasses.dataclass(frozen=True)
class EvidenceReference:
    """135I §11.1."""

    evidence_id: str
    evidence_kind: str
    reference: str
    outcome_summary: MappingProxyType = dataclasses.field(default_factory=lambda: MappingProxyType({}))
    captured_at: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.evidence_id:
            raise ValueError("EvidenceReference.evidence_id is required")
        if not self.reference:
            raise ValueError("EvidenceReference.reference is required")
        object.__setattr__(self, "outcome_summary", _deep_freeze(dict(self.outcome_summary)))


@dataclasses.dataclass(frozen=True)
class ShadowTransitionInput:
    """The one explicit shadow-transition input object (phase 135K brief).

    Every field here must be supplied explicitly by the production caller
    (i.e. the shared shadow integration service invoked from
    ``run_finalization_transaction``). This object never reconstructs a
    missing field from report title, task title, filename, Architecture
    Status title, commit subject, git log, repository HEAD, latest-file
    presence, or stale metadata — a caller with an unresolved field passes
    ``None`` explicitly and the construction step (``shadow.py``) turns
    that into a named, disclosed shadow failure, never a guess.
    """

    entry_point: str
    phase_id: str
    transition_type: TransitionType
    intended_lifecycle_state: LifecycleState
    source_revision: Optional[str]
    repository_identity: Optional[str]
    branch_identity: Optional[str]

    task_id: Optional[str] = None
    predecessor_transition_id: Optional[str] = None
    final_revision: Optional[str] = None

    phase_commit_ownership: tuple[CommitOwnershipEntry, ...] = ()
    evidence_refs: tuple[EvidenceReference, ...] = ()

    report_id: Optional[str] = None
    report_digest: Optional[str] = None
    metadata_id: Optional[str] = None
    metadata_digest: Optional[str] = None
    snapshot_id: Optional[str] = None
    snapshot_digest: Optional[str] = None
    checkpoint_id: Optional[str] = None
    promotion_id: Optional[str] = None

    notification_ids: tuple[str, ...] = ()
    notification_state: NotificationState = NotificationState.NOT_ATTEMPTED
    notification_suppressed: bool = False

    marker_id: Optional[str] = None
    receipt_id: Optional[str] = None

    recovery_classification_hint: Optional[RecoveryClassification] = None
    failure_classification: Optional[FailureClassification] = None
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "phase_commit_ownership", tuple(self.phase_commit_ownership))
        object.__setattr__(self, "evidence_refs", tuple(self.evidence_refs))
        object.__setattr__(self, "notification_ids", tuple(self.notification_ids))
        object.__setattr__(self, "limitations", tuple(self.limitations))


@dataclasses.dataclass(frozen=True)
class RepresentationBinding:
    """135I §5 — identity + digest binding for one representation kind, as
    carried inside the record (not the adapter's comparison output, which
    lives in ``adapters.py``)."""

    identity: Optional[str]
    digest: Optional[str]
    authority_role: AuthorityRole


@dataclasses.dataclass(frozen=True)
class InvariantEvaluation:
    """135I §12.2."""

    invariant_id: str
    category: str
    evaluation_result: str
    blocking_classification: str
    explanatory_text: str
    evidence_references: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


@dataclasses.dataclass(frozen=True)
class ProductionCltrRecord:
    """The production, immutable CLTR record (135I §7's field catalog).

    This is always a **shadow** record: constructed strictly from a
    ``ShadowTransitionInput`` the caller supplied and never claiming
    authority over the production lifecycle it observes.
    """

    schema_id: str
    schema_version: str
    contract_version: str
    compatibility_id: str

    transition_id: str
    phase_id: str
    repository_identity: str
    branch_identity: str
    transition_type: TransitionType
    lifecycle_state: LifecycleState
    source_revision: str

    task_id: Optional[str] = None
    final_revision: Optional[str] = None
    prior_state: Optional[str] = None  # transition_id of predecessor, or "none"

    certified_state: Optional[MappingProxyType] = None
    projected_state: Optional[MappingProxyType] = None

    overlay_flags: tuple[str, ...] = ()

    phase_commit_ownership: tuple[CommitOwnershipEntry, ...] = ()
    evidence_refs: tuple[EvidenceReference, ...] = ()

    report_id: Optional[str] = None
    report_digest: Optional[str] = None
    metadata_id: Optional[str] = None
    metadata_digest: Optional[str] = None
    snapshot_id: Optional[str] = None
    snapshot_digest: Optional[str] = None
    checkpoint_id: Optional[str] = None
    promotion_id: Optional[str] = None

    notification_ids: tuple[str, ...] = ()
    notification_state: NotificationState = NotificationState.NOT_ATTEMPTED
    notification_suppressed: bool = False

    marker_id: Optional[str] = None
    receipt_id: Optional[str] = None

    predecessor_transition_id: Optional[str] = None
    successor_transition_id: Optional[str] = None

    failure_classification: Optional[str] = None
    retry_classification: str = RetryClassification.NOT_RETRYABLE_TERMINAL.value
    recovery_classification: str = RecoveryClassification.NONE_REQUIRED.value
    terminal_classification: str = TerminalClassification.NON_TERMINAL.value

    timestamps: MappingProxyType = dataclasses.field(default_factory=lambda: MappingProxyType({}))
    event_history: tuple[MappingProxyType, ...] = ()

    limitations: tuple[str, ...] = ()
    compatibility_metadata: MappingProxyType = dataclasses.field(default_factory=lambda: MappingProxyType({}))

    #: 135K non-authority disclosure — encoded on every record (phase
    #: brief §23), never relying on documentation alone.
    shadow_mode: bool = True
    authoritative: bool = False
    entry_point: str = ""

    record_digest: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.transition_id:
            raise ValueError("ProductionCltrRecord.transition_id is required")
        if not self.phase_id:
            raise ValueError("ProductionCltrRecord.phase_id is required")
        if not self.source_revision:
            raise ValueError("ProductionCltrRecord.source_revision is required")
        if self.schema_version != schema.SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version for construction: {self.schema_version!r}")
        object.__setattr__(self, "certified_state", _deep_freeze(dict(self.certified_state or {})))
        object.__setattr__(self, "projected_state", _deep_freeze(dict(self.projected_state or {})))
        object.__setattr__(self, "timestamps", _deep_freeze(dict(self.timestamps)))
        object.__setattr__(self, "event_history", tuple(_deep_freeze(dict(e)) for e in self.event_history))
        object.__setattr__(self, "compatibility_metadata", _deep_freeze(dict(self.compatibility_metadata)))
        object.__setattr__(self, "overlay_flags", tuple(self.overlay_flags))
        object.__setattr__(self, "phase_commit_ownership", tuple(self.phase_commit_ownership))
        object.__setattr__(self, "evidence_refs", tuple(self.evidence_refs))
        object.__setattr__(self, "notification_ids", tuple(self.notification_ids))
        object.__setattr__(self, "limitations", tuple(self.limitations))

    def with_digest(self, digest: str) -> "ProductionCltrRecord":
        return dataclasses.replace(self, record_digest=digest)

    @property
    def is_certified_or_later(self) -> bool:
        from pcae.cltr.enums import CERTIFIED_OR_LATER_STATES

        return self.lifecycle_state in CERTIFIED_OR_LATER_STATES
