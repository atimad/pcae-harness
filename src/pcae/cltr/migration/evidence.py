"""Canonical Stage 1 migration-evidence record (phase brief §22).

Evidence, not lifecycle authority: never consulted by either derivation
path as an input, never determines whether a finalization transaction
completes, and is always disclosed as non-authoritative.
"""

from __future__ import annotations

import dataclasses
from typing import Optional

from pcae.cltr.digest import compute_dict_digest
from pcae.cltr.migration.comparison import ComparisonResult
from pcae.cltr.migration.disclosure import NON_AUTHORITY_DISCLOSURE
from pcae.cltr.migration.enums import (
    NON_PROGRESSABLE_RECOVERY_CLASSIFICATIONS,
    ComparisonResultClass,
    MigrationRecoveryClassification,
    MigrationStage,
    ProductionAuthority,
)

EVIDENCE_SCHEMA_ID = "CLTR-MIGRATION-EVIDENCE-001"
EVIDENCE_SCHEMA_VERSION = "1.0.0"


@dataclasses.dataclass(frozen=True)
class MigrationEvidenceRecord:
    evidence_schema_id: str
    evidence_schema_version: str
    migration_stage: MigrationStage
    migration_epoch: str
    authority_epoch: str
    production_authority: ProductionAuthority
    package_id: str
    transition_id: str
    entry_point: str
    input_revision_digests: tuple[str, ...]
    legacy_derivation_digest: Optional[str]
    cltr_derivation_digest: Optional[str]
    comparison_overall_class: ComparisonResultClass
    comparison_field_results: tuple[dict, ...]
    recovery_classification: MigrationRecoveryClassification
    production_completion_continued: bool
    migration_progression_eligible: bool
    limitations: tuple[str, ...]
    created_at: str
    evidence_digest: Optional[str] = None

    def digestible_payload(self) -> dict:
        payload = dataclasses.asdict(self)
        payload.pop("evidence_digest", None)
        payload["migration_stage"] = self.migration_stage.value
        payload["production_authority"] = self.production_authority.value
        payload["comparison_overall_class"] = self.comparison_overall_class.value
        payload["recovery_classification"] = self.recovery_classification.value
        return payload

    def with_digest(self, digest: str) -> "MigrationEvidenceRecord":
        return dataclasses.replace(self, evidence_digest=digest)


def compute_evidence_digest(record: MigrationEvidenceRecord) -> str:
    return compute_dict_digest(record.digestible_payload())


def determine_progression_eligibility(
    *, comparison: ComparisonResult, recovery_classification: MigrationRecoveryClassification, migration_failed: bool
) -> bool:
    """Phase brief §33 -- deterministic, advisory-only eligibility. False
    on any authority-relevant mismatch, on unverifiable critical fields,
    on migration failure, or on a non-progressable recovery
    classification (135H.1 escape prevention, §27)."""

    if migration_failed:
        return False
    if comparison.authority_relevant_mismatch:
        return False
    if comparison.unverifiable:
        return False
    if recovery_classification in NON_PROGRESSABLE_RECOVERY_CLASSIFICATIONS:
        return False
    return True


def build_evidence(
    *,
    migration_stage: MigrationStage,
    migration_epoch: str,
    authority_epoch: str,
    package_id: str,
    transition_id: str,
    entry_point: str,
    input_revision_digests: tuple[str, ...],
    legacy_derivation_digest: Optional[str],
    cltr_derivation_digest: Optional[str],
    comparison: ComparisonResult,
    recovery_classification: MigrationRecoveryClassification,
    production_completion_continued: bool,
    limitations: tuple[str, ...] = (),
    migration_failed: bool = False,
) -> MigrationEvidenceRecord:
    from pcae.cltr.migration.persistence import timestamp

    eligible = determine_progression_eligibility(
        comparison=comparison, recovery_classification=recovery_classification, migration_failed=migration_failed
    )
    record = MigrationEvidenceRecord(
        evidence_schema_id=EVIDENCE_SCHEMA_ID,
        evidence_schema_version=EVIDENCE_SCHEMA_VERSION,
        migration_stage=migration_stage,
        migration_epoch=migration_epoch,
        authority_epoch=authority_epoch,
        production_authority=ProductionAuthority.LEGACY,
        package_id=package_id,
        transition_id=transition_id,
        entry_point=entry_point,
        input_revision_digests=tuple(input_revision_digests),
        legacy_derivation_digest=legacy_derivation_digest,
        cltr_derivation_digest=cltr_derivation_digest,
        comparison_overall_class=comparison.overall_class,
        comparison_field_results=tuple(
            {
                "field": c.field,
                "result_class": c.result_class.value,
                "legacy_value": c.legacy_value,
                "cltr_value": c.cltr_value,
                "detail": c.detail,
            }
            for c in comparison.comparisons
        ),
        recovery_classification=recovery_classification,
        production_completion_continued=production_completion_continued,
        migration_progression_eligible=eligible,
        limitations=tuple(limitations),
        created_at=timestamp(),
    )
    digest = compute_evidence_digest(record)
    return record.with_digest(digest)
