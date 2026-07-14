"""Stage 1 CLTR derivation adapter (phase brief §14).

Reuses the existing production CLTR package unchanged: construction,
CLTR-SCHEMA-001 v1.0.1 validation, all 37 invariants, and the 15
representation adapters. Never publishes into the shadow generation
store (avoids two competing "current" pointers for one transition --
phase brief §32); the derivation result is migration evidence only,
persisted exclusively in the migration namespace (``evidence.py`` /
``persistence.py``).

Consumes the *same* shared input revision the legacy derivation consumed
-- it never derives CLTR fields from the legacy normalized output (phase
brief §14, "Both paths must derive independently from shared explicit
inputs").
"""

from __future__ import annotations

import dataclasses
from typing import Optional

from pcae.cltr import schema
from pcae.cltr.adapters import AdapterResult, AdapterSources, run_all_adapters
from pcae.cltr.digest import compute_record_digest
from pcae.cltr.enums import (
    CERTIFIED_OR_LATER_STATES,
    LifecycleState,
    NotificationState,
    TransitionType,
    derive_recovery_classification,
    derive_retry_classification,
    derive_terminal_classification,
)
from pcae.cltr.invariants import InvariantContext, evaluate_all, has_blocking_failure
from pcae.cltr.migration.enums import InputStage
from pcae.cltr.migration.shared_input import SharedTransitionInputPackage
from pcae.cltr.models import CommitOwnershipEntry, InvariantEvaluation, ProductionCltrRecord
from pcae.cltr.validation import ValidationError, validate_record


def _normalize_commit_ownership(package: SharedTransitionInputPackage) -> tuple[CommitOwnershipEntry, ...]:
    """Phase 135S — fixes F-135P-3: ``phase_commit_ownership`` may arrive
    on the shared input as bare commit-hash strings (135M §8.4 captures
    only the hash, not a full ownership record). Normalizes each into a
    typed ``CommitOwnershipEntry`` the same way the Stage-0 shadow
    observer already does (``finalization_transaction.py``'s
    ``commit_ownership`` construction), rather than forwarding raw
    strings that would later crash ``CLTR-COMMIT-2``'s
    ``.certification_state`` dereference. Any entry already typed is
    passed through unchanged."""

    from pcae.cltr.enums import CertificationState

    raw = package.field("phase_commit_ownership") or ()
    entries = []
    for item in raw:
        if isinstance(item, CommitOwnershipEntry):
            entries.append(item)
            continue
        entries.append(
            CommitOwnershipEntry(
                commit_hash=str(item),
                repository_identity=package.phase_id,
                branch_identity="main",
                # Honest disclosure, matching the Stage-0 shadow
                # observer's own precedent: production does not yet
                # implement the three-outcome commit-ownership
                # verification model (135H §1, 135J F5) -- Stage 1/Stage 2
                # derivation never fabricates a `verified` classification.
                certification_state=CertificationState.UNVERIFIABLE,
            )
        )
    return tuple(entries)


@dataclasses.dataclass(frozen=True)
class CltrDerivationResult:
    status: str  # "constructed" | "missing_mandatory_input" | "validation_failed" | "invariant_failed"
    transition_id: str
    input_revision_digest: Optional[str]
    record: Optional[ProductionCltrRecord]
    record_digest: Optional[str]
    validation_errors: tuple[ValidationError, ...]
    invariant_evaluations: tuple[InvariantEvaluation, ...]
    adapter_results: tuple[AdapterResult, ...]
    limitations: tuple[str, ...]
    shadow_mode: bool = True
    authoritative: bool = False


def derive_cltr(
    package: SharedTransitionInputPackage,
    *,
    adapter_sources: AdapterSources | None = None,
) -> CltrDerivationResult:
    consumed_completion = any(r.stage == InputStage.LEGACY_COMPLETION for r in package.revisions)
    if not consumed_completion:
        return CltrDerivationResult(
            status="missing_mandatory_input",
            transition_id=package.transition_id,
            input_revision_digest=package.latest.revision_digest,
            record=None,
            record_digest=None,
            validation_errors=(),
            invariant_evaluations=(),
            adapter_results=(),
            limitations=("legacy-completion revision not yet enriched: CLTR derivation deferred",),
        )

    notification_state_raw = package.field("notification_state")
    lifecycle_state_raw = package.field("lifecycle_state")
    transition_type_raw = package.field("transition_type")

    try:
        lifecycle_state = LifecycleState(lifecycle_state_raw) if lifecycle_state_raw else LifecycleState.TERMINAL_PARTIAL_EXTERNAL
        transition_type = TransitionType(transition_type_raw) if transition_type_raw else TransitionType.CLOSE_PARTIAL
        notification_state = (
            NotificationState(notification_state_raw) if notification_state_raw else NotificationState.NOT_ATTEMPTED
        )
    except ValueError as exc:
        return CltrDerivationResult(
            status="validation_failed",
            transition_id=package.transition_id,
            input_revision_digest=package.latest.revision_digest,
            record=None,
            record_digest=None,
            validation_errors=(),
            invariant_evaluations=(),
            adapter_results=(),
            limitations=(f"malformed lifecycle/transition/notification value: {exc}",),
        )

    certified_state = None
    if lifecycle_state in CERTIFIED_OR_LATER_STATES:
        certified_state = {
            "report_id": package.field("report_id"),
            "metadata_id": package.field("metadata_id"),
            "snapshot_id": package.field("snapshot_id"),
        }

    try:
        record = ProductionCltrRecord(
            schema_id=schema.SCHEMA_ID,
            schema_version=schema.SCHEMA_VERSION,
            contract_version=schema.CONTRACT_VERSION,
            compatibility_id=schema.COMPATIBILITY_ID,
            transition_id=package.transition_id,
            phase_id=package.phase_id,
            task_id=package.field("task_id"),
            repository_identity=package.phase_id,
            branch_identity="main",
            transition_type=transition_type,
            lifecycle_state=lifecycle_state,
            source_revision=package.field("source_revision"),
            final_revision=package.field("staged_final_revision"),
            prior_state=package.predecessor_transition_id or "none",
            certified_state=certified_state,
            phase_commit_ownership=_normalize_commit_ownership(package),
            report_id=package.field("report_id"),
            report_digest=package.field("report_digest"),
            metadata_id=package.field("metadata_id"),
            metadata_digest=package.field("metadata_digest"),
            snapshot_id=package.field("snapshot_id"),
            snapshot_digest=package.field("snapshot_digest"),
            checkpoint_id=package.field("checkpoint_id"),
            promotion_id=package.field("promotion_id"),
            notification_ids=package.field("notification_ids") or (),
            notification_state=notification_state,
            notification_suppressed=bool(package.field("notification_suppressed")),
            marker_id=package.field("marker_id"),
            receipt_id=package.field("receipt_id"),
            predecessor_transition_id=package.predecessor_transition_id,
            retry_classification=derive_retry_classification(lifecycle_state).value,
            recovery_classification=derive_recovery_classification(lifecycle_state).value,
            terminal_classification=derive_terminal_classification(lifecycle_state).value,
            limitations=(
                "Stage 1 dual-derivation CLTR record: derived from the shared transition-input "
                "package, not published into the shadow generation store (135O phase brief §32).",
            ),
            compatibility_metadata={"produced_by": "pcae.cltr.migration (135O)", "shadow_mode": True},
            entry_point=package.entry_point,
        )
    except ValueError as exc:
        return CltrDerivationResult(
            status="missing_mandatory_input",
            transition_id=package.transition_id,
            input_revision_digest=package.latest.revision_digest,
            record=None,
            record_digest=None,
            validation_errors=(),
            invariant_evaluations=(),
            adapter_results=(),
            limitations=(str(exc),),
        )

    validation_errors = validate_record(record)
    if validation_errors:
        return CltrDerivationResult(
            status="validation_failed",
            transition_id=package.transition_id,
            input_revision_digest=package.latest.revision_digest,
            record=record,
            record_digest=None,
            validation_errors=validation_errors,
            invariant_evaluations=(),
            adapter_results=(),
            limitations=(),
        )

    invariant_evaluations = evaluate_all(record, InvariantContext())
    record_digest = compute_record_digest(record)
    digested_record = record.with_digest(record_digest)
    adapter_results = run_all_adapters(digested_record, adapter_sources or AdapterSources())

    if has_blocking_failure(invariant_evaluations):
        return CltrDerivationResult(
            status="invariant_failed",
            transition_id=package.transition_id,
            input_revision_digest=package.latest.revision_digest,
            record=digested_record,
            record_digest=record_digest,
            validation_errors=(),
            invariant_evaluations=invariant_evaluations,
            adapter_results=adapter_results,
            limitations=(),
        )

    return CltrDerivationResult(
        status="constructed",
        transition_id=package.transition_id,
        input_revision_digest=package.latest.revision_digest,
        record=digested_record,
        record_digest=record_digest,
        validation_errors=(),
        invariant_evaluations=invariant_evaluations,
        adapter_results=adapter_results,
        limitations=(),
    )
