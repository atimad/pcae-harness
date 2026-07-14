"""The shared shadow integration service (phase 135K brief §1, §22-§29).

``observe_finalized_transition`` is the ONE function every production entry
point calls (via ``run_finalization_transaction``, the shared boundary all
four entry points already funnel through — 135H). It is deliberately the
only place that:

  1. constructs a ``ProductionCltrRecord`` from an explicit
     ``ShadowTransitionInput`` (no narrative fallback, §5 of models.py),
  2. validates it against CLTR-SCHEMA-001 v1.0.1,
  3. runs all 37 invariants,
  4. canonicalizes and digests it,
  5. persists an immutable generation and atomically publishes the current
     pointer (success path), or persists a failure artifact (failure path),
  6. runs the 15 representation adapters and records comparison outcomes.

This function never raises to its caller for an ordinary shadow-side
defect — every outcome is a ``ShadowObservationResult`` value. It is safe
to call unconditionally from production code: a shadow failure is recorded
and disclosed, never propagated as a production exception (phase brief
§33, "shadow failure does not automatically block current production
completion").
"""

from __future__ import annotations

import dataclasses
import os

from pcae.cltr import schema
from pcae.cltr.adapters import AdapterResult, AdapterSources, run_all_adapters
from pcae.cltr.digest import compute_record_digest
from pcae.cltr.enums import (
    derive_recovery_classification,
    derive_retry_classification,
    derive_terminal_classification,
)
from pcae.cltr.invariants import InvariantContext, evaluate_all, has_blocking_failure
from pcae.cltr.models import InvariantEvaluation, ProductionCltrRecord, ShadowTransitionInput
from pcae.cltr.persistence import DEFAULT_SHADOW_ROOT, GenerationHandle, persist_failure, publish_generation
from pcae.cltr.validation import ValidationError, validate_record

FEATURE_FLAG_ENV_VAR = "PCAE_CLTR_SHADOW_ENABLED"


def is_shadow_enabled() -> bool:
    """135K brief §32 — disabled by default; existing repo convention for
    boolean env flags (``.lower() in ("1", "true", "yes")``)."""

    return os.environ.get(FEATURE_FLAG_ENV_VAR, "").strip().lower() in ("1", "true", "yes")


@dataclasses.dataclass(frozen=True)
class ShadowObservationResult:
    status: str  # "missing_mandatory_input" | "validation_failed" | "invariant_failed" | "published" | "publish_failed"
    phase_id: str
    entry_point: str
    transition_id: str | None = None
    record_digest: str | None = None
    generation_directory: str | None = None
    construction_errors: tuple[str, ...] = ()
    validation_errors: tuple[ValidationError, ...] = ()
    invariant_evaluations: tuple[InvariantEvaluation, ...] = ()
    adapter_results: tuple[AdapterResult, ...] = ()
    limitations: tuple[str, ...] = ()
    shadow_mode: bool = True
    authoritative: bool = False


_MANDATORY_FIELDS = (
    "phase_id",
    "transition_type",
    "intended_lifecycle_state",
    "source_revision",
    "repository_identity",
    "branch_identity",
)


def _check_mandatory_input(shadow_input: ShadowTransitionInput) -> tuple[str, ...]:
    missing = []
    for field_name in _MANDATORY_FIELDS:
        if getattr(shadow_input, field_name) in (None, ""):
            missing.append(field_name)
    return tuple(missing)


def _construct_record(shadow_input: ShadowTransitionInput) -> ProductionCltrRecord:
    terminal_classification = derive_terminal_classification(shadow_input.intended_lifecycle_state)
    retry_classification = derive_retry_classification(shadow_input.intended_lifecycle_state)
    recovery_classification = shadow_input.recovery_classification_hint or derive_recovery_classification(
        shadow_input.intended_lifecycle_state
    )
    certified_state = None
    from pcae.cltr.enums import CERTIFIED_OR_LATER_STATES

    if shadow_input.intended_lifecycle_state in CERTIFIED_OR_LATER_STATES:
        certified_state = {
            "report_id": shadow_input.report_id,
            "metadata_id": shadow_input.metadata_id,
            "snapshot_id": shadow_input.snapshot_id,
        }

    return ProductionCltrRecord(
        schema_id=schema.SCHEMA_ID,
        schema_version=schema.SCHEMA_VERSION,
        contract_version=schema.CONTRACT_VERSION,
        compatibility_id=schema.COMPATIBILITY_ID,
        transition_id=shadow_input.phase_id,
        phase_id=shadow_input.phase_id,
        task_id=shadow_input.task_id,
        repository_identity=shadow_input.repository_identity,
        branch_identity=shadow_input.branch_identity,
        transition_type=shadow_input.transition_type,
        lifecycle_state=shadow_input.intended_lifecycle_state,
        source_revision=shadow_input.source_revision,
        final_revision=shadow_input.final_revision,
        prior_state=shadow_input.predecessor_transition_id or "none",
        certified_state=certified_state,
        phase_commit_ownership=shadow_input.phase_commit_ownership,
        evidence_refs=shadow_input.evidence_refs,
        report_id=shadow_input.report_id,
        report_digest=shadow_input.report_digest,
        metadata_id=shadow_input.metadata_id,
        metadata_digest=shadow_input.metadata_digest,
        snapshot_id=shadow_input.snapshot_id,
        snapshot_digest=shadow_input.snapshot_digest,
        checkpoint_id=shadow_input.checkpoint_id,
        promotion_id=shadow_input.promotion_id,
        notification_ids=shadow_input.notification_ids,
        notification_state=shadow_input.notification_state,
        notification_suppressed=shadow_input.notification_suppressed,
        marker_id=shadow_input.marker_id,
        receipt_id=shadow_input.receipt_id,
        predecessor_transition_id=shadow_input.predecessor_transition_id,
        failure_classification=shadow_input.failure_classification.value if shadow_input.failure_classification else None,
        retry_classification=retry_classification.value,
        recovery_classification=recovery_classification.value,
        terminal_classification=terminal_classification.value,
        limitations=shadow_input.limitations,
        compatibility_metadata={"produced_by": "pcae.cltr (135K)", "shadow_mode": True},
        entry_point=shadow_input.entry_point,
    )


def observe_finalized_transition(
    shadow_input: ShadowTransitionInput,
    *,
    adapter_sources: AdapterSources | None = None,
    shadow_root=DEFAULT_SHADOW_ROOT,
) -> ShadowObservationResult:
    """Construct, validate, digest, persist, and compare exactly one shadow
    CLTR record for an already-finalized production transition.

    Never raises for an ordinary shadow-side defect. Always returns a
    disclosed, non-authoritative result.
    """

    missing = _check_mandatory_input(shadow_input)
    if missing:
        detail = {"missing_fields": list(missing), "entry_point": shadow_input.entry_point}
        persist_failure(
            phase_id=shadow_input.phase_id or "unknown-phase",
            entry_point=shadow_input.entry_point,
            failure_stage="construction",
            detail=detail,
            shadow_root=shadow_root,
        )
        return ShadowObservationResult(
            status="missing_mandatory_input",
            phase_id=shadow_input.phase_id or "",
            entry_point=shadow_input.entry_point,
            construction_errors=missing,
        )

    try:
        record = _construct_record(shadow_input)
    except ValueError as exc:
        persist_failure(
            phase_id=shadow_input.phase_id,
            entry_point=shadow_input.entry_point,
            failure_stage="construction",
            detail={"error": str(exc)},
            shadow_root=shadow_root,
        )
        return ShadowObservationResult(
            status="missing_mandatory_input",
            phase_id=shadow_input.phase_id,
            entry_point=shadow_input.entry_point,
            construction_errors=(str(exc),),
        )

    validation_errors = validate_record(record)
    if validation_errors:
        persist_failure(
            phase_id=record.phase_id,
            entry_point=shadow_input.entry_point,
            failure_stage="validation",
            detail={"errors": [dataclasses.asdict(e) for e in validation_errors]},
            shadow_root=shadow_root,
        )
        return ShadowObservationResult(
            status="validation_failed",
            phase_id=record.phase_id,
            entry_point=shadow_input.entry_point,
            transition_id=record.transition_id,
            validation_errors=validation_errors,
        )

    invariant_evaluations = evaluate_all(record, InvariantContext())
    blocking_failure = has_blocking_failure(invariant_evaluations)

    record_digest = compute_record_digest(record)
    digested_record = record.with_digest(record_digest)

    adapter_results = run_all_adapters(digested_record, adapter_sources or AdapterSources())

    if blocking_failure:
        persist_failure(
            phase_id=record.phase_id,
            entry_point=shadow_input.entry_point,
            failure_stage="invariants",
            detail={
                "record_digest": record_digest,
                "failures": [
                    dataclasses.asdict(e) for e in invariant_evaluations if e.evaluation_result == "fail"
                ],
            },
            shadow_root=shadow_root,
        )
        return ShadowObservationResult(
            status="invariant_failed",
            phase_id=record.phase_id,
            entry_point=shadow_input.entry_point,
            transition_id=record.transition_id,
            record_digest=record_digest,
            invariant_evaluations=invariant_evaluations,
            adapter_results=adapter_results,
        )

    try:
        handle: GenerationHandle = publish_generation(
            digested_record, entry_point=shadow_input.entry_point, shadow_root=shadow_root
        )
    except Exception as exc:  # noqa: BLE001 - shadow persistence failure must never propagate
        persist_failure(
            phase_id=record.phase_id,
            entry_point=shadow_input.entry_point,
            failure_stage="publication",
            detail={"error": f"{type(exc).__name__}: {exc}", "record_digest": record_digest},
            shadow_root=shadow_root,
        )
        return ShadowObservationResult(
            status="publish_failed",
            phase_id=record.phase_id,
            entry_point=shadow_input.entry_point,
            transition_id=record.transition_id,
            record_digest=record_digest,
            invariant_evaluations=invariant_evaluations,
            adapter_results=adapter_results,
            limitations=(f"publication failed: {type(exc).__name__}: {exc}",),
        )

    return ShadowObservationResult(
        status="published",
        phase_id=record.phase_id,
        entry_point=shadow_input.entry_point,
        transition_id=record.transition_id,
        record_digest=record_digest,
        generation_directory=str(handle.directory),
        invariant_evaluations=invariant_evaluations,
        adapter_results=adapter_results,
    )


def observe_finalized_transition_best_effort(
    shadow_input: ShadowTransitionInput,
    *,
    adapter_sources: AdapterSources | None = None,
    shadow_root=DEFAULT_SHADOW_ROOT,
) -> ShadowObservationResult | None:
    """Entry-point-facing wrapper: returns ``None`` (no-op) when the shadow
    feature flag is disabled, and never lets an unexpected exception escape
    into the caller's production finalization path (phase brief §33:
    "shadow failure does not automatically block current production
    completion")."""

    if not is_shadow_enabled():
        return None
    try:
        return observe_finalized_transition(shadow_input, adapter_sources=adapter_sources, shadow_root=shadow_root)
    except Exception as exc:  # noqa: BLE001 - absolute last-resort containment boundary
        try:
            persist_failure(
                phase_id=shadow_input.phase_id or "unknown-phase",
                entry_point=shadow_input.entry_point,
                failure_stage="unexpected",
                detail={"error": f"{type(exc).__name__}: {exc}"},
                shadow_root=shadow_root,
            )
        except Exception:  # noqa: BLE001 - even failure persistence must not propagate
            pass
        return ShadowObservationResult(
            status="publish_failed",
            phase_id=shadow_input.phase_id or "",
            entry_point=shadow_input.entry_point,
            limitations=(f"unexpected shadow error contained: {type(exc).__name__}: {exc}",),
        )
