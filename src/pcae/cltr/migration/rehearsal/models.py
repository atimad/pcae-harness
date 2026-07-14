"""Stage 2 rehearsal dataclasses (135Q §6/§9/§18/§23/§33)."""

from __future__ import annotations

import dataclasses
from typing import Optional

from pcae.cltr.migration.rehearsal.enums import ArtifactRole, CandidateKind, RehearsalOutcome, VerificationStatus


@dataclasses.dataclass(frozen=True)
class CandidateArtifact:
    """One of 135Q §9's file-producing candidate artifacts."""

    kind: CandidateKind
    artifact_role: ArtifactRole
    verification_status: VerificationStatus
    content: dict
    digest: Optional[str] = None

    def with_digest(self, digest: str) -> "CandidateArtifact":
        return dataclasses.replace(self, digest=digest)

    @property
    def filename(self) -> str:
        return f"{self.kind.value}.json"


@dataclasses.dataclass(frozen=True)
class RehearsalManifest:
    """135Q §18's manifest contract. ``manifest_schema_version`` follows
    CLTR-SCHEMA-001 §2's semver rules independently, per 135Q §18."""

    manifest_schema_id: str
    manifest_schema_version: str
    rehearsal_generation_id: str
    migration_epoch: str
    authority_epoch: str
    transition_id: str
    shared_input_package_id: str
    final_input_revision_digest: str
    artifact_inventory: tuple[dict, ...]
    derivation_sources: dict
    comparison_results: dict
    verification_status: str
    limitations: tuple[str, ...]
    candidate_or_authoritative_role: str
    pointer_target_data: dict
    digest_algorithm: str
    non_authority_disclosure: dict
    generation_digest: Optional[str] = None

    def digestible_payload(self) -> dict:
        payload = dataclasses.asdict(self)
        payload.pop("generation_digest", None)
        return payload

    def with_digest(self, digest: str) -> "RehearsalManifest":
        return dataclasses.replace(self, generation_digest=digest)


@dataclasses.dataclass(frozen=True)
class RehearsalPointer:
    """135Q §23's rehearsal-only pointer content."""

    rehearsal_generation_id: str
    migration_epoch: str
    authority_epoch: str
    transition_id: str
    generation_digest: str
    non_authority_disclosure: dict


@dataclasses.dataclass(frozen=True)
class RehearsalEvidenceRecord:
    """135Q §33's Stage 2 evidence record."""

    evidence_id: str
    schema_version: str
    migration_stage: str
    migration_epoch: str
    authority_epoch: str
    production_authority: str
    transition_id: str
    shared_input_package_id: str
    final_input_revision_digest: str
    stage1_evidence_digest: Optional[str]
    rehearsal_generation_id: Optional[str]
    manifest_digest: Optional[str]
    generation_digest: Optional[str]
    outcome: RehearsalOutcome
    pointer_result: str
    comparison_summary: dict
    mismatch_classes: tuple[str, ...]
    crash_recovery_state: Optional[str]
    progression_eligibility: bool
    limitations: tuple[str, ...]
    non_authority_disclosure: dict
    created_at: str
    record_digest: Optional[str] = None

    def digestible_payload(self) -> dict:
        payload = dataclasses.asdict(self)
        payload.pop("record_digest", None)
        payload["outcome"] = self.outcome.value
        return payload

    def with_digest(self, digest: str) -> "RehearsalEvidenceRecord":
        return dataclasses.replace(self, record_digest=digest)
