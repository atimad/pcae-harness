"""Dual-derivation coordinator (phase brief §15-§16).

The one shared object every entry point calls, twice per finalization
attempt: once at the pre-transaction identity-resolution point
(``capture_pre_transaction``), once after legacy's finalization sequence
has completed (``complete``). Never decides production certification,
promotion, notification dispatch, marker/receipt creation, or task
state; never grants CLTR authority. Every stage failure is isolated,
persisted as failure evidence, and never propagates -- exactly the
existing shadow-integration containment discipline (``shadow.py``'s
``observe_finalized_transition_best_effort``).
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Optional

from pcae.cltr.adapters import AdapterSources
from pcae.cltr.migration.assembly import SharedInputValidationError, assemble_pre_transaction, enrich_legacy_completion
from pcae.cltr.migration.cltr_derivation import derive_cltr
from pcae.cltr.migration.comparison import compare
from pcae.cltr.migration.configuration import MigrationConfiguration, MigrationConfigurationError, load_configuration
from pcae.cltr.migration.disclosure import NON_AUTHORITY_DISCLOSURE as _SHARED_DISCLOSURE
from pcae.cltr.migration.enums import MigrationRecoveryClassification, MigrationStage, ProductionAuthority
from pcae.cltr.migration.evidence import MigrationEvidenceRecord, build_evidence
from pcae.cltr.migration.legacy_derivation import derive_legacy
from pcae.cltr.migration.persistence import (
    DEFAULT_MIGRATION_ROOT,
    transition_dir,
    write_atomic,
    write_immutable,
)
from pcae.cltr.migration.shared_input import SharedTransitionInputPackage
from pcae.cltr.migration.transition_identity import resolve_transition_id

NON_AUTHORITY_DISCLOSURE = {**_SHARED_DISCLOSURE, "migration_stage": None}


@dataclasses.dataclass(frozen=True)
class MigrationResult:
    status: str
    stage_failed: Optional[str] = None
    package: Optional[SharedTransitionInputPackage] = None
    evidence: Optional[MigrationEvidenceRecord] = None
    migration_progression_eligible: bool = False
    limitations: tuple[str, ...] = ()
    non_authority_disclosure: dict = dataclasses.field(default_factory=lambda: dict(NON_AUTHORITY_DISCLOSURE))


def _persist_failure(migration_root: Path, *, migration_epoch: str, transition_id: str, stage: str, detail: dict) -> None:
    from pcae.cltr.migration.persistence import new_uuid, safe_join
    from pcae.cltr.canonicalization import canonicalize_dict

    try:
        directory = transition_dir(migration_root, migration_epoch or "unknown-epoch", transition_id or "unknown-transition")
        failures_dir = safe_join(directory, "failures")
        write_atomic(failures_dir / f"{new_uuid()}.json", canonicalize_dict({"stage": stage, "detail": detail}))
    except Exception:  # noqa: BLE001 - failure persistence must never itself raise
        pass


def capture_pre_transaction(
    *,
    phase_id: str,
    entry_point: str,
    source_revision: str,
    staged_final_revision: Optional[str],
    phase_commit_ownership: tuple,
    intended_transition: str,
    recovery_classification: MigrationRecoveryClassification,
    task_id: Optional[str] = None,
    limitations: tuple[str, ...] = (),
    migration_root: Path = DEFAULT_MIGRATION_ROOT,
    configuration: Optional[MigrationConfiguration] = None,
) -> Optional[SharedTransitionInputPackage]:
    """Returns ``None`` (no-op) when Stage 1 is not effectively active.
    Never raises for an ordinary migration-side defect; a construction or
    persistence failure is recorded and this returns ``None`` so the
    caller proceeds exactly as if dual derivation were disabled."""

    try:
        config = configuration if configuration is not None else load_configuration()
    except MigrationConfigurationError:
        return None
    if not config.effectively_active:
        return None

    try:
        identity = resolve_transition_id(
            phase_id=phase_id,
            entry_point=entry_point,
            migration_epoch=config.migration_epoch,
            source_revision=source_revision,
            migration_root=migration_root,
        )
        authority_epoch = _authority_epoch(config)
        package = assemble_pre_transaction(
            migration_epoch=config.migration_epoch,
            authority_epoch=authority_epoch,
            phase_id=phase_id,
            entry_point=entry_point,
            transition_id=identity.transition_id,
            predecessor_transition_id=identity.predecessor_transition_id,
            fields={
                "phase_id": phase_id,
                "task_id": task_id,
                "entry_point": entry_point,
                "source_revision": source_revision,
                "staged_final_revision": staged_final_revision,
                "phase_commit_ownership": tuple(phase_commit_ownership),
                "intended_transition": intended_transition,
                "predecessor_transition_id": identity.predecessor_transition_id,
                "recovery_classification": recovery_classification.value,
            },
            limitations=limitations,
        )
        _persist_revision(migration_root, package, package.latest)
        return package
    except (SharedInputValidationError, ValueError, OSError) as exc:
        _persist_failure(
            migration_root,
            migration_epoch=config.migration_epoch or "unknown-epoch",
            transition_id="unresolved",
            stage="input_assembly",
            detail={"error": f"{type(exc).__name__}: {exc}", "phase_id": phase_id, "entry_point": entry_point},
        )
        return None


def _authority_epoch(config: MigrationConfiguration) -> str:
    from pcae.cltr import schema

    return "|".join(
        [
            ProductionAuthority.LEGACY.value,
            config.migration_stage.value,
            config.migration_epoch or "",
            schema.SCHEMA_ID,
            schema.SCHEMA_VERSION,
        ]
    )


def _persist_revision(migration_root: Path, package: SharedTransitionInputPackage, revision) -> None:
    from pcae.cltr.canonicalization import canonicalize_dict

    directory = transition_dir(migration_root, package.migration_epoch, package.transition_id)
    inputs_dir = directory / "inputs"
    payload = dict(revision.digestible_payload())
    payload["revision_digest"] = revision.revision_digest
    write_immutable(inputs_dir / f"{revision.revision}.json", canonicalize_dict(payload))


def complete(
    package: SharedTransitionInputPackage,
    *,
    legacy_completion_fields: dict,
    recovery_classification: MigrationRecoveryClassification,
    production_completion_continued: bool,
    adapter_sources: Optional[AdapterSources] = None,
    limitations: tuple[str, ...] = (),
    migration_root: Path = DEFAULT_MIGRATION_ROOT,
    configuration: Optional[MigrationConfiguration] = None,
) -> MigrationResult:
    """Stage-B/C/D-collapsed enrichment (135M §8.4) plus dual derivation,
    comparison, and evidence persistence. Never raises; every failure
    stage returns a disclosed ``MigrationResult`` with
    ``migration_progression_eligible=False``."""

    try:
        config = configuration if configuration is not None else load_configuration()
    except MigrationConfigurationError as exc:
        return MigrationResult(status="config_invalid", stage_failed="configuration", limitations=(str(exc),))
    if not config.effectively_active:
        return MigrationResult(status="disabled")

    stage = "input_assembly"
    try:
        package = enrich_legacy_completion(package, fields=legacy_completion_fields, limitations=limitations)
        _persist_revision(migration_root, package, package.latest)

        stage = "legacy_derivation"
        legacy_result = derive_legacy(package)

        stage = "cltr_derivation"
        cltr_result = derive_cltr(package, adapter_sources=adapter_sources)

        stage = "comparison"
        comparison_result = compare(legacy_result, cltr_result)

        stage = "migration_evidence"
        evidence = build_evidence(
            migration_stage=config.migration_stage,
            migration_epoch=config.migration_epoch,
            authority_epoch=package.authority_epoch,
            package_id=package.package_id,
            transition_id=package.transition_id,
            entry_point=package.entry_point,
            input_revision_digests=tuple(r.revision_digest for r in package.revisions),
            legacy_derivation_digest=legacy_result.derivation_digest,
            cltr_derivation_digest=cltr_result.record_digest,
            comparison=comparison_result,
            recovery_classification=recovery_classification,
            production_completion_continued=production_completion_continued,
            limitations=legacy_result.limitations + cltr_result.limitations,
        )

        stage = "persistence"
        _persist_evidence(migration_root, package, evidence)

        return MigrationResult(
            status="completed",
            package=package,
            evidence=evidence,
            migration_progression_eligible=evidence.migration_progression_eligible,
            limitations=evidence.limitations,
        )
    except Exception as exc:  # noqa: BLE001 - migration failure must never affect production finalization
        _persist_failure(
            migration_root,
            migration_epoch=config.migration_epoch or "unknown-epoch",
            transition_id=package.transition_id if isinstance(package, SharedTransitionInputPackage) else "unresolved",
            stage=stage,
            detail={"error": f"{type(exc).__name__}: {exc}"},
        )
        return MigrationResult(status="failed", stage_failed=stage, limitations=(f"{type(exc).__name__}: {exc}",))


def _persist_evidence(migration_root: Path, package: SharedTransitionInputPackage, evidence: MigrationEvidenceRecord) -> None:
    from pcae.cltr.canonicalization import canonicalize_dict
    from pcae.cltr.migration.persistence import safe_join

    directory = transition_dir(migration_root, package.migration_epoch, package.transition_id)
    evidence_dir = safe_join(directory, "evidence")
    payload = evidence.digestible_payload()
    payload["evidence_digest"] = evidence.evidence_digest
    write_immutable(evidence_dir / "evidence.json", canonicalize_dict(payload))

    status_dir = migration_root / "status"
    pointer = {
        "migration_epoch": package.migration_epoch,
        "transition_id": package.transition_id,
        "evidence_digest": evidence.evidence_digest,
        "migration_progression_eligible": evidence.migration_progression_eligible,
    }
    write_atomic(status_dir / "current-evidence", canonicalize_dict(pointer))


def run_stage1_best_effort_pre_transaction(**kwargs) -> Optional[SharedTransitionInputPackage]:
    """Entry-point-facing wrapper matching ``shadow.py``'s
    ``observe_finalized_transition_best_effort`` naming convention."""

    try:
        return capture_pre_transaction(**kwargs)
    except Exception:  # noqa: BLE001 - absolute last-resort containment boundary
        return None


def run_stage1_best_effort_completion(package, **kwargs) -> Optional[MigrationResult]:
    if package is None:
        return None
    try:
        return complete(package, **kwargs)
    except Exception:  # noqa: BLE001 - absolute last-resort containment boundary
        return None
