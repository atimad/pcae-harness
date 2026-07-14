"""Staged shared-input assembly, repaired and verified by 135N (135M §8.4,
quoted in ``enums.InputStage``'s docstring).

Two capture points only, matching §8.4 exactly:

  * ``assemble_pre_transaction`` -- pre-transaction facts, assembled once,
    before either derivation path begins.
  * ``enrich_legacy_completion`` -- in-transaction completion identities,
    captured from legacy's own already-completed sequential path, at the
    same point ``_observe_shadow_cltr`` already occupies. Produces a new,
    additional, immutable revision; the prior revision is never mutated.
"""

from __future__ import annotations

from pcae.cltr.migration.enums import InputStage
from pcae.cltr.migration.shared_input import (
    FieldProvenance,
    SharedInputRevision,
    SharedTransitionInputPackage,
    compute_package_id,
    compute_revision_digest,
)

#: Fields §8.4 designates "pre-transaction facts" -- assemblable, and
#: required, before either derivation path begins.
PRE_TRANSACTION_FIELDS = (
    "phase_id",
    "task_id",
    "entry_point",
    "source_revision",
    "staged_final_revision",
    "phase_commit_ownership",
    "intended_transition",
    "predecessor_transition_id",
    "recovery_classification",
)

#: Fields §8.4 designates "in-transaction completion identities" -- must
#: never appear in the pre-transaction revision (premature-field
#: rejection, phase brief §6/§12).
LEGACY_COMPLETION_FIELDS = (
    "transition_type",
    "lifecycle_state",
    "report_id",
    "report_digest",
    "metadata_id",
    "metadata_digest",
    "snapshot_id",
    "snapshot_digest",
    "checkpoint_id",
    "promotion_id",
    "notification_ids",
    "notification_state",
    "notification_suppressed",
    "marker_id",
    "receipt_id",
)

_REQUIRED_PRE_TRANSACTION = ("phase_id", "entry_point", "source_revision", "intended_transition", "recovery_classification")


class SharedInputValidationError(ValueError):
    """Fail-closed: a missing required field or a premature field for the
    current stage is never silently repaired from narrative or mutable
    files."""


def assemble_pre_transaction(
    *,
    migration_epoch: str,
    authority_epoch: str,
    phase_id: str,
    entry_point: str,
    transition_id: str,
    predecessor_transition_id: str | None,
    fields: dict,
    limitations: tuple[str, ...] = (),
) -> SharedTransitionInputPackage:
    missing = [name for name in _REQUIRED_PRE_TRANSACTION if fields.get(name) in (None, "")]
    if missing:
        raise SharedInputValidationError(f"missing mandatory Stage-1 pre-transaction field(s): {missing}")
    premature = [name for name in LEGACY_COMPLETION_FIELDS if name in fields]
    if premature:
        raise SharedInputValidationError(
            f"premature legacy-completion field(s) present before legacy's finalization path has run: {premature}"
        )

    package_id = compute_package_id(
        migration_epoch=migration_epoch,
        authority_epoch=authority_epoch,
        phase_id=phase_id,
        transition_id=transition_id,
        entry_point=entry_point,
        predecessor_transition_id=predecessor_transition_id,
    )

    provenance = {
        name: FieldProvenance(
            source_component="finalization_transaction.run_finalization_transaction",
            source_authority="legacy",
            observation_stage=InputStage.PRE_TRANSACTION,
            verification_state="explicit",
            source_field=name,
        )
        for name in fields
    }

    revision = SharedInputRevision(
        package_id=package_id,
        stage=InputStage.PRE_TRANSACTION,
        revision=1,
        predecessor_digest=None,
        fields=dict(fields),
        provenance=provenance,
        newly_available_fields=tuple(sorted(fields)),
        created_reason="pre-transaction identity capture (135M §8.4, before either derivation path begins)",
        limitations=limitations,
    )
    revision = revision.with_digest(compute_revision_digest(revision))

    return SharedTransitionInputPackage(
        package_id=package_id,
        migration_epoch=migration_epoch,
        authority_epoch=authority_epoch,
        phase_id=phase_id,
        entry_point=entry_point,
        transition_id=transition_id,
        predecessor_transition_id=predecessor_transition_id,
        revisions=(revision,),
    )


def enrich_legacy_completion(
    package: SharedTransitionInputPackage,
    *,
    fields: dict,
    limitations: tuple[str, ...] = (),
) -> SharedTransitionInputPackage:
    prior = package.latest
    if prior.stage != InputStage.PRE_TRANSACTION:
        raise SharedInputValidationError(
            f"cannot enrich a package whose latest revision is already {prior.stage.value!r}"
        )
    unknown = [name for name in fields if name not in LEGACY_COMPLETION_FIELDS]
    if unknown:
        raise SharedInputValidationError(f"unexpected field(s) for legacy-completion enrichment: {unknown}")

    provenance = {
        name: FieldProvenance(
            source_component="finalization_transaction._observe_shadow_cltr",
            source_authority="legacy",
            observation_stage=InputStage.LEGACY_COMPLETION,
            verification_state="explicit",
            source_field=name,
        )
        for name in fields
    }

    revision = SharedInputRevision(
        package_id=package.package_id,
        stage=InputStage.LEGACY_COMPLETION,
        revision=prior.revision + 1,
        predecessor_digest=prior.revision_digest,
        fields=dict(fields),
        provenance=provenance,
        newly_available_fields=tuple(sorted(fields)),
        created_reason=(
            "legacy-completion enrichment (135M §8.4, captured from legacy's own completed "
            "sequential finalization path)"
        ),
        limitations=limitations,
    )
    revision = revision.with_digest(compute_revision_digest(revision))
    return package.with_revision(revision)
