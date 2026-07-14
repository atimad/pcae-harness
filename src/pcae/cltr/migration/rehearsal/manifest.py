"""Stage 2 manifest construction and verification (135Q §18/§19/§38)."""

from __future__ import annotations

from pcae.cltr.migration.disclosure import NON_AUTHORITY_DISCLOSURE
from pcae.cltr.migration.rehearsal.comparison import RehearsalComparisonSummary
from pcae.cltr.migration.rehearsal.configuration import MANIFEST_SCHEMA_ID, MANIFEST_SCHEMA_VERSION
from pcae.cltr.migration.rehearsal.digest import DIGEST_ALGORITHM, compute_artifact_digest, compute_generation_digest
from pcae.cltr.migration.rehearsal.enums import CANDIDATE_ORDER, CRITICAL_KINDS, VerificationStatus
from pcae.cltr.migration.rehearsal.models import CandidateArtifact, RehearsalManifest


class ManifestVerificationError(ValueError):
    """Fail-closed: never silently repaired (135Q §22's "no repair by
    inference" rule, applied to manifest verification)."""


def digest_candidates(candidates: dict) -> dict:
    """Digests every candidate independently, in §19's fixed canonical
    order (never directory-listing order). Returns kind-value -> digested
    ``CandidateArtifact``."""

    digested = {}
    for kind in CANDIDATE_ORDER:
        artifact = candidates[kind]
        digested[kind] = artifact.with_digest(compute_artifact_digest(artifact.content))
    return digested


def build_manifest(
    *,
    rehearsal_generation_id: str,
    migration_epoch: str,
    authority_epoch: str,
    transition_id: str,
    shared_input_package_id: str,
    final_input_revision_digest: str,
    digested_candidates: dict,
    comparison_summary: RehearsalComparisonSummary,
    limitations: tuple[str, ...],
) -> RehearsalManifest:
    artifact_inventory = []
    for kind in CANDIDATE_ORDER:
        artifact: CandidateArtifact = digested_candidates[kind]
        artifact_inventory.append(
            {
                "artifact_kind": kind.value,
                "path": artifact.filename,
                "digest": artifact.digest,
                "artifact_role": artifact.artifact_role.value,
                "verification_status": artifact.verification_status.value,
            }
        )

    any_critical_unverifiable = any(
        digested_candidates[kind].verification_status == VerificationStatus.UNVERIFIABLE for kind in CRITICAL_KINDS
    )
    generation_verification_status = "unverifiable" if any_critical_unverifiable else "verified"

    manifest = RehearsalManifest(
        manifest_schema_id=MANIFEST_SCHEMA_ID,
        manifest_schema_version=MANIFEST_SCHEMA_VERSION,
        rehearsal_generation_id=rehearsal_generation_id,
        migration_epoch=migration_epoch,
        authority_epoch=authority_epoch,
        transition_id=transition_id,
        shared_input_package_id=shared_input_package_id,
        final_input_revision_digest=final_input_revision_digest,
        artifact_inventory=tuple(artifact_inventory),
        derivation_sources={kind.value: "legacy_completion_enrichment" for kind in CANDIDATE_ORDER},
        comparison_results={
            "stage1_overall_class": comparison_summary.stage1_overall_class.value,
            "stage1_authority_relevant_mismatch": comparison_summary.stage1_authority_relevant_mismatch,
            "stage1_unverifiable": comparison_summary.stage1_unverifiable,
            "expected_difference_kinds": list(comparison_summary.expected_difference_kinds),
            "mismatch_classes": list(comparison_summary.mismatch_classes),
        },
        verification_status=generation_verification_status,
        limitations=tuple(limitations)
        + (
            "items 11-14 of 135Q §9's 23-item inventory (git-attribution view, "
            "compatibility/legacy-format view [optional], diagnostic envelope "
            "[optional], reconciliation view) are not emitted as separate files "
            "in this implementation: git attribution is folded into the "
            "commit-attribution candidate, the two optional views are disclosed "
            "as not produced, and the reconciliation view is computed on demand "
            "by the read-only reconcile command rather than stored.",
        ),
        candidate_or_authoritative_role="rehearsal_candidate_generation",
        pointer_target_data={
            "rehearsal_generation_id": rehearsal_generation_id,
            "migration_epoch": migration_epoch,
            "authority_epoch": authority_epoch,
            "transition_id": transition_id,
        },
        digest_algorithm=DIGEST_ALGORITHM,
        non_authority_disclosure=dict(NON_AUTHORITY_DISCLOSURE),
    )

    ordered_digests = tuple(digested_candidates[kind].digest for kind in CANDIDATE_ORDER)
    generation_digest = compute_generation_digest(
        artifact_digests_in_order=ordered_digests,
        rehearsal_generation_id=rehearsal_generation_id,
        migration_epoch=migration_epoch,
        authority_epoch=authority_epoch,
        transition_id=transition_id,
    )
    return manifest.with_digest(generation_digest)


def verify_manifest(manifest: RehearsalManifest, digested_candidates: dict) -> None:
    """Recomputes every artifact digest and the generation digest, fails
    closed on any mismatch (135Q §19's tamper-detection contract). Also
    checks §38's split-brain cross-reference requirement: every
    candidate's own ``rehearsal_generation_id``/``transition_id`` must
    agree with the manifest's."""

    if manifest.digest_algorithm != DIGEST_ALGORITHM:
        raise ManifestVerificationError(f"unsupported digest_algorithm: {manifest.digest_algorithm!r}")

    for entry in manifest.artifact_inventory:
        kind_value = entry["artifact_kind"]
        matching = [k for k in digested_candidates if k.value == kind_value]
        if not matching:
            raise ManifestVerificationError(f"manifest references unknown artifact kind: {kind_value!r}")
        artifact = digested_candidates[matching[0]]
        recomputed = compute_artifact_digest(artifact.content)
        if recomputed != entry["digest"] or recomputed != artifact.digest:
            raise ManifestVerificationError(f"artifact digest mismatch for {kind_value!r}")
        if artifact.content.get("rehearsal_generation_id") != manifest.rehearsal_generation_id:
            raise ManifestVerificationError(f"split-brain: {kind_value!r} bound to a different rehearsal_generation_id")
        if artifact.content.get("transition_id") != manifest.transition_id:
            raise ManifestVerificationError(f"split-brain: {kind_value!r} bound to a different transition_id")

    ordered_digests = tuple(digested_candidates[kind].digest for kind in CANDIDATE_ORDER)
    recomputed_generation_digest = compute_generation_digest(
        artifact_digests_in_order=ordered_digests,
        rehearsal_generation_id=manifest.rehearsal_generation_id,
        migration_epoch=manifest.migration_epoch,
        authority_epoch=manifest.authority_epoch,
        transition_id=manifest.transition_id,
    )
    if recomputed_generation_digest != manifest.generation_digest:
        raise ManifestVerificationError("generation digest mismatch")
