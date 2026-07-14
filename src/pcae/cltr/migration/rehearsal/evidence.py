"""Stage 2 evidence record construction and persistence (135Q §33)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pcae.cltr.canonicalization import canonicalize_dict
from pcae.cltr.digest import compute_dict_digest
from pcae.cltr.migration.disclosure import NON_AUTHORITY_DISCLOSURE
from pcae.cltr.migration.persistence import timestamp, write_atomic, write_immutable
from pcae.cltr.migration.rehearsal.comparison import RehearsalComparisonSummary
from pcae.cltr.migration.rehearsal.enums import RehearsalOutcome
from pcae.cltr.migration.rehearsal.identity import PRODUCTION_AUTHORITY_DISCLOSURE, REHEARSAL_STAGE
from pcae.cltr.migration.rehearsal.models import RehearsalEvidenceRecord
from pcae.cltr.migration.rehearsal.persistence import generations_dir, rehearsal_evidence_pointer_path

EVIDENCE_SCHEMA_VERSION = "1.0.0"


def build_evidence(
    *,
    migration_epoch: str,
    authority_epoch: str,
    transition_id: str,
    shared_input_package_id: str,
    final_input_revision_digest: str,
    stage1_evidence_digest: Optional[str],
    rehearsal_generation_id: Optional[str],
    manifest_digest: Optional[str],
    generation_digest: Optional[str],
    outcome: RehearsalOutcome,
    pointer_result: str,
    comparison_summary: Optional[RehearsalComparisonSummary],
    crash_recovery_state: Optional[str],
    progression_eligibility: bool,
    limitations: tuple[str, ...] = (),
) -> RehearsalEvidenceRecord:
    evidence_id = compute_dict_digest(
        {
            "rehearsal_generation_id": rehearsal_generation_id,
            "transition_id": transition_id,
            "outcome": outcome.value,
        }
    )
    record = RehearsalEvidenceRecord(
        evidence_id=evidence_id,
        schema_version=EVIDENCE_SCHEMA_VERSION,
        migration_stage=REHEARSAL_STAGE,
        migration_epoch=migration_epoch,
        authority_epoch=authority_epoch,
        production_authority=PRODUCTION_AUTHORITY_DISCLOSURE,
        transition_id=transition_id,
        shared_input_package_id=shared_input_package_id,
        final_input_revision_digest=final_input_revision_digest,
        stage1_evidence_digest=stage1_evidence_digest,
        rehearsal_generation_id=rehearsal_generation_id,
        manifest_digest=manifest_digest,
        generation_digest=generation_digest,
        outcome=outcome,
        pointer_result=pointer_result,
        comparison_summary=(
            {
                "stage1_overall_class": comparison_summary.stage1_overall_class.value,
                "stage1_authority_relevant_mismatch": comparison_summary.stage1_authority_relevant_mismatch,
                "stage1_unverifiable": comparison_summary.stage1_unverifiable,
            }
            if comparison_summary is not None
            else {}
        ),
        mismatch_classes=comparison_summary.mismatch_classes if comparison_summary is not None else (),
        crash_recovery_state=crash_recovery_state,
        progression_eligibility=progression_eligibility,
        limitations=tuple(limitations),
        non_authority_disclosure=dict(NON_AUTHORITY_DISCLOSURE),
        created_at=timestamp(),
    )
    digest = compute_dict_digest(record.digestible_payload())
    return record.with_digest(digest)


def persist_evidence(migration_root: Path, record: RehearsalEvidenceRecord) -> None:
    if record.rehearsal_generation_id is not None:
        gen_dir = generations_dir(
            migration_root, record.migration_epoch, record.transition_id, record.rehearsal_generation_id
        )
        payload = record.digestible_payload()
        payload["record_digest"] = record.record_digest
        write_immutable(gen_dir / "rehearsal_evidence.json", canonicalize_dict(payload))

    pointer_payload = {
        "migration_epoch": record.migration_epoch,
        "transition_id": record.transition_id,
        "rehearsal_generation_id": record.rehearsal_generation_id,
        "outcome": record.outcome.value,
        "record_digest": record.record_digest,
        "progression_eligibility": record.progression_eligibility,
    }
    write_atomic(rehearsal_evidence_pointer_path(migration_root), canonicalize_dict(pointer_payload))
