"""Stage 2 rehearsal coordinator (135Q §17/§20-§30/§39).

The one shared coordinator every production entry point invokes,
identically, through ``_run_stage2_atomic_rehearsal`` in
``pcae.core.finalization_transaction`` -- no entry-point-specific
publication semantics (135Q §39). Implements the candidate-assembly
sequence, precondition contract, mismatch policy, atomic pointer
publication, quarantine, idempotent replay, and evidence recording.
Never raises into its caller; every failure is contained and recorded as
disclosed, non-authoritative evidence (mirrors
``pcae.cltr.migration.coordinator``'s own containment discipline).

Fault injection (135Q §52) is exposed only through the optional
``fault_injector`` callable parameter, which no production call site
ever supplies -- it exists solely for this package's own test suite to
exercise the crash matrix (135Q §26) deterministically.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Callable, Optional

from pcae.cltr.canonicalization import canonicalize_dict
from pcae.cltr.migration import comparison as stage1_comparison_mod
from pcae.cltr.migration.cltr_derivation import CltrDerivationResult
from pcae.cltr.migration.enums import InputStage
from pcae.cltr.migration.legacy_derivation import LegacyDerivationResult
from pcae.cltr.migration.persistence import new_uuid, write_atomic
from pcae.cltr.migration.rehearsal import candidates as candidate_builders
from pcae.cltr.migration.rehearsal.comparison import summarize
from pcae.cltr.migration.rehearsal.configuration import RehearsalConfiguration, load_rehearsal_configuration
from pcae.cltr.migration.rehearsal.digest import compute_artifact_digest
from pcae.cltr.migration.rehearsal.enums import CANDIDATE_ORDER, CheckpointState, RehearsalOutcome
from pcae.cltr.migration.rehearsal.evidence import build_evidence, persist_evidence
from pcae.cltr.migration.rehearsal.identity import compute_rehearsal_generation_id
from pcae.cltr.migration.rehearsal.manifest import ManifestVerificationError, build_manifest, digest_candidates, verify_manifest
from pcae.cltr.migration.rehearsal.persistence import (
    DEFAULT_MIGRATION_ROOT,
    RehearsalPersistenceError,
    candidates_dir,
    failures_dir,
    finalize_generation,
    generations_dir,
    quarantine_dir,
    read_generation_artifacts,
    read_json,
)
from pcae.cltr.migration.rehearsal.pointer import PointerRejectedError, publish, verify_published_target
from pcae.cltr.migration.shared_input import SharedTransitionInputPackage
from pcae.cltr import schema as cltr_schema

FaultInjector = Callable[[str], None]


@dataclasses.dataclass(frozen=True)
class RehearsalResult:
    outcome: RehearsalOutcome
    rehearsal_generation_id: Optional[str] = None
    generation_digest: Optional[str] = None
    progression_eligibility: bool = False
    limitations: tuple[str, ...] = ()


def _no_op_injector(_step: str) -> None:
    return None


def _precondition_failures(
    *,
    config: RehearsalConfiguration,
    package: SharedTransitionInputPackage,
    stage1_status: str,
    stage1_comparison: stage1_comparison_mod.ComparisonResult,
) -> list[str]:
    failures: list[str] = []
    if not config.effectively_active:
        failures.append("Stage 2 rehearsal is not effectively active (flag disabled or Stage 1 inactive)")
        return failures
    if not any(r.stage == InputStage.LEGACY_COMPLETION for r in package.revisions):
        failures.append("shared input package has no LEGACY_COMPLETION-stage revision yet")
    if stage1_status != "completed":
        failures.append(f"Stage 1 evidence is not in a completed state: {stage1_status!r}")
    if stage1_comparison.authority_relevant_mismatch:
        failures.append("Stage 1 comparison recorded an authority-relevant mismatch for this transition")
    if not package.migration_epoch:
        failures.append("missing migration_epoch")
    if not package.authority_epoch:
        failures.append("missing authority_epoch")
    return failures


def _build_candidates(
    *,
    rehearsal_generation_id: str,
    package: SharedTransitionInputPackage,
    cltr: CltrDerivationResult,
    legacy: LegacyDerivationResult,
    runtime_snapshot: dict,
) -> dict:
    notification = candidate_builders.build_notification_intent_candidate(
        rehearsal_generation_id=rehearsal_generation_id,
        package=package,
        report_digest=legacy.fields.get("report_digest"),
    )
    marker = candidate_builders.build_marker_candidate(
        rehearsal_generation_id=rehearsal_generation_id,
        package=package,
        notification_id=notification.content["notification_id"],
        report_digest=legacy.fields.get("report_digest"),
    )
    receipt = candidate_builders.build_receipt_candidate(
        rehearsal_generation_id=rehearsal_generation_id,
        package=package,
        marker_id=marker.content["marker_candidate_id"],
        notification_id=notification.content["notification_id"],
    )
    checkpoint = candidate_builders.build_checkpoint_candidate(
        rehearsal_generation_id=rehearsal_generation_id,
        package=package,
        state=CheckpointState.GENERATION_PREPARATION.value,
    )
    return {
        artifact.kind: artifact
        for artifact in [
            candidate_builders.build_cltr_record_candidate(
                rehearsal_generation_id=rehearsal_generation_id, package=package, cltr=cltr
            ),
            candidate_builders.build_report_candidate(
                rehearsal_generation_id=rehearsal_generation_id, package=package, legacy=legacy
            ),
            candidate_builders.build_metadata_candidate(
                rehearsal_generation_id=rehearsal_generation_id, package=package, legacy=legacy
            ),
            candidate_builders.build_architecture_status_candidate(
                rehearsal_generation_id=rehearsal_generation_id, package=package, runtime_snapshot=runtime_snapshot
            ),
            checkpoint,
            notification,
            marker,
            receipt,
            candidate_builders.build_commit_attribution_candidate(
                rehearsal_generation_id=rehearsal_generation_id, package=package, cltr=cltr
            ),
            candidate_builders.build_repository_transition_candidate(
                rehearsal_generation_id=rehearsal_generation_id, package=package
            ),
        ]
    }


def _persist_failure(migration_root: Path, *, migration_epoch: str, transition_id: str, step: str, detail: dict) -> None:
    try:
        directory = failures_dir(migration_root, migration_epoch or "unknown-epoch", transition_id or "unknown-transition")
        write_atomic(directory / f"{new_uuid()}.json", canonicalize_dict({"step": step, "detail": detail}))
    except Exception:  # noqa: BLE001 - failure persistence must never itself raise
        pass


def _persist_quarantine(migration_root: Path, *, migration_epoch: str, transition_id: str, rehearsal_generation_id: str, reason: str) -> None:
    try:
        directory = quarantine_dir(migration_root, migration_epoch, transition_id, rehearsal_generation_id)
        write_atomic(directory / "quarantine_record.json", canonicalize_dict({"reason": reason, "rehearsal_generation_id": rehearsal_generation_id}))
    except Exception:  # noqa: BLE001
        pass


def run_stage2_rehearsal(
    *,
    package: SharedTransitionInputPackage,
    stage1_status: str,
    stage1_evidence_digest: Optional[str],
    cltr_result: CltrDerivationResult,
    legacy_result: LegacyDerivationResult,
    stage1_comparison_result: stage1_comparison_mod.ComparisonResult,
    runtime_snapshot: dict,
    migration_root: Path = DEFAULT_MIGRATION_ROOT,
    configuration: Optional[RehearsalConfiguration] = None,
    fault_injector: FaultInjector = _no_op_injector,
) -> RehearsalResult:
    step = "configuration"
    try:
        config = configuration if configuration is not None else load_rehearsal_configuration()
    except Exception as exc:  # noqa: BLE001 - fail closed, never raise
        return RehearsalResult(outcome=RehearsalOutcome.REJECTED_PRECONDITION, limitations=(f"{type(exc).__name__}: {exc}",))

    if not config.atomic_rehearsal_enabled:
        return RehearsalResult(outcome=RehearsalOutcome.REJECTED_PRECONDITION, limitations=("Stage 2 rehearsal disabled",))

    step = "preconditions"
    try:
        fault_injector(step)
        failures = _precondition_failures(
            config=config, package=package, stage1_status=stage1_status, stage1_comparison=stage1_comparison_result
        )
        if failures:
            evidence = build_evidence(
                migration_epoch=package.migration_epoch,
                authority_epoch=package.authority_epoch,
                transition_id=package.transition_id,
                shared_input_package_id=package.package_id,
                final_input_revision_digest=package.latest.revision_digest or "",
                stage1_evidence_digest=stage1_evidence_digest,
                rehearsal_generation_id=None,
                manifest_digest=None,
                generation_digest=None,
                outcome=RehearsalOutcome.REJECTED_PRECONDITION,
                pointer_result="not_attempted",
                comparison_summary=None,
                crash_recovery_state="before_candidate_creation",
                progression_eligibility=False,
                limitations=tuple(failures),
            )
            persist_evidence(migration_root, evidence)
            return RehearsalResult(outcome=RehearsalOutcome.REJECTED_PRECONDITION, limitations=tuple(failures))

        step = "identity"
        rehearsal_generation_id = compute_rehearsal_generation_id(
            migration_epoch=package.migration_epoch,
            authority_epoch=package.authority_epoch,
            transition_id=package.transition_id,
            shared_input_package_id=package.package_id,
            final_input_revision_digest=package.latest.revision_digest or "",
            phase_id=package.phase_id,
            task_id=package.field("task_id"),
            schema_versions={
                "cltr_schema_version": cltr_schema.SCHEMA_VERSION,
                "manifest_schema_version": "1.0.0",
            },
        )

        step = "idempotency_check"
        existing_generation_dir = generations_dir(migration_root, package.migration_epoch, package.transition_id, rehearsal_generation_id)
        existing_manifest = read_json(existing_generation_dir / "manifest.json")
        if existing_manifest is not None:
            return RehearsalResult(
                outcome=RehearsalOutcome.IDEMPOTENT_REPLAY,
                rehearsal_generation_id=rehearsal_generation_id,
                generation_digest=existing_manifest.get("generation_digest"),
                progression_eligibility=bool(existing_manifest.get("verification_status") == "verified"),
            )

        step = "candidate_directory_creation"
        fault_injector(step)
        candidate_dir = candidates_dir(migration_root, package.migration_epoch, package.transition_id, rehearsal_generation_id)
        candidate_dir.mkdir(parents=True, exist_ok=True)

        step = "candidate_derivation"
        candidates = _build_candidates(
            rehearsal_generation_id=rehearsal_generation_id,
            package=package,
            cltr=cltr_result,
            legacy=legacy_result,
            runtime_snapshot=runtime_snapshot,
        )

        step = "candidate_write"
        for kind in CANDIDATE_ORDER:
            fault_injector(f"before_write_{kind.value}")
            artifact = candidates[kind]
            (candidate_dir / artifact.filename).write_text(
                canonicalize_dict(artifact.content).decode("utf-8"), encoding="utf-8"
            )
            fault_injector(f"after_write_{kind.value}")

        step = "digest_candidates"
        digested = digest_candidates(candidates)

        step = "comparison_summary"
        comparison_summary = summarize(stage1_comparison_result)

        step = "manifest_write"
        fault_injector("before_manifest_write")
        manifest = build_manifest(
            rehearsal_generation_id=rehearsal_generation_id,
            migration_epoch=package.migration_epoch,
            authority_epoch=package.authority_epoch,
            transition_id=package.transition_id,
            shared_input_package_id=package.package_id,
            final_input_revision_digest=package.latest.revision_digest or "",
            digested_candidates=digested,
            comparison_summary=comparison_summary,
            limitations=legacy_result.limitations + cltr_result.limitations,
        )
        manifest_payload = manifest.digestible_payload()
        manifest_payload["generation_digest"] = manifest.generation_digest
        (candidate_dir / "manifest.json").write_bytes(canonicalize_dict(manifest_payload))
        fault_injector("after_manifest_write")

        step = "verification"
        fault_injector(step)
        verify_manifest(manifest, digested)

        step = "policy"
        blocked_by_mismatch = comparison_summary.blocks_publication
        progression_eligibility = not blocked_by_mismatch

        step = "finalization"
        fault_injector("before_finalization")
        generation_dir = generations_dir(migration_root, package.migration_epoch, package.transition_id, rehearsal_generation_id)
        finalize_generation(candidate_dir, generation_dir)
        fault_injector("after_finalization")

        if blocked_by_mismatch:
            evidence = build_evidence(
                migration_epoch=package.migration_epoch,
                authority_epoch=package.authority_epoch,
                transition_id=package.transition_id,
                shared_input_package_id=package.package_id,
                final_input_revision_digest=package.latest.revision_digest or "",
                stage1_evidence_digest=stage1_evidence_digest,
                rehearsal_generation_id=rehearsal_generation_id,
                manifest_digest=manifest.generation_digest,
                generation_digest=manifest.generation_digest,
                outcome=RehearsalOutcome.BLOCKED_BY_MISMATCH,
                pointer_result="not_attempted",
                comparison_summary=comparison_summary,
                crash_recovery_state="rehearsal_terminal_state",
                progression_eligibility=False,
                limitations=manifest.limitations,
            )
            persist_evidence(migration_root, evidence)
            return RehearsalResult(
                outcome=RehearsalOutcome.BLOCKED_BY_MISMATCH,
                rehearsal_generation_id=rehearsal_generation_id,
                generation_digest=manifest.generation_digest,
                progression_eligibility=False,
                limitations=manifest.limitations,
            )

        step = "pointer_publication"
        fault_injector("before_pointer_publish")
        try:
            publish(migration_root=migration_root, manifest=manifest)
        except PointerRejectedError as exc:
            _persist_quarantine(
                migration_root,
                migration_epoch=package.migration_epoch,
                transition_id=package.transition_id,
                rehearsal_generation_id=rehearsal_generation_id,
                reason=str(exc),
            )
            evidence = build_evidence(
                migration_epoch=package.migration_epoch,
                authority_epoch=package.authority_epoch,
                transition_id=package.transition_id,
                shared_input_package_id=package.package_id,
                final_input_revision_digest=package.latest.revision_digest or "",
                stage1_evidence_digest=stage1_evidence_digest,
                rehearsal_generation_id=rehearsal_generation_id,
                manifest_digest=manifest.generation_digest,
                generation_digest=manifest.generation_digest,
                outcome=RehearsalOutcome.QUARANTINED,
                pointer_result="rejected",
                comparison_summary=comparison_summary,
                crash_recovery_state="quarantine_required",
                progression_eligibility=False,
                limitations=(str(exc),),
            )
            persist_evidence(migration_root, evidence)
            return RehearsalResult(
                outcome=RehearsalOutcome.QUARANTINED, rehearsal_generation_id=rehearsal_generation_id, limitations=(str(exc),)
            )
        fault_injector("after_pointer_publish")

        step = "pointer_verification"
        fault_injector(step)
        verified = verify_published_target(migration_root, package.migration_epoch, package.transition_id, rehearsal_generation_id)
        pointer_result = "published_and_verified" if verified else "publication_uncertain"
        outcome = RehearsalOutcome.SUCCESSFUL if verified else RehearsalOutcome.UNCERTAIN_PUBLICATION
        progression_eligibility = progression_eligibility and verified

        step = "evidence_recording"
        fault_injector("before_evidence_persist")
        evidence = build_evidence(
            migration_epoch=package.migration_epoch,
            authority_epoch=package.authority_epoch,
            transition_id=package.transition_id,
            shared_input_package_id=package.package_id,
            final_input_revision_digest=package.latest.revision_digest or "",
            stage1_evidence_digest=stage1_evidence_digest,
            rehearsal_generation_id=rehearsal_generation_id,
            manifest_digest=manifest.generation_digest,
            generation_digest=manifest.generation_digest,
            outcome=outcome,
            pointer_result=pointer_result,
            comparison_summary=comparison_summary,
            crash_recovery_state="rehearsal_terminal_state" if verified else "pointer_publication_uncertain",
            progression_eligibility=progression_eligibility,
            limitations=manifest.limitations,
        )
        persist_evidence(migration_root, evidence)
        fault_injector("after_evidence_persist")

        return RehearsalResult(
            outcome=outcome,
            rehearsal_generation_id=rehearsal_generation_id,
            generation_digest=manifest.generation_digest,
            progression_eligibility=progression_eligibility,
            limitations=manifest.limitations,
        )
    except Exception as exc:  # noqa: BLE001 - Stage 2 failure must never affect production finalization
        _persist_failure(
            migration_root,
            migration_epoch=package.migration_epoch if package is not None else "unknown-epoch",
            transition_id=package.transition_id if package is not None else "unresolved",
            step=step,
            detail={"error": f"{type(exc).__name__}: {exc}"},
        )
        return RehearsalResult(outcome=RehearsalOutcome.FAILED, limitations=(f"{step}: {type(exc).__name__}: {exc}",))


def run_stage2_best_effort(**kwargs) -> Optional[RehearsalResult]:
    """Entry-point-facing wrapper matching
    ``pcae.cltr.migration.coordinator.run_stage1_best_effort_completion``'s
    naming convention -- absolute last-resort containment boundary."""

    try:
        return run_stage2_rehearsal(**kwargs)
    except Exception:  # noqa: BLE001
        return None
