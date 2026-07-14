"""Stage 2 rehearsal-generation identity (135Q §6).

Deterministic composite -- never timestamp-derived, never random, never
title/Git-history-derived. An unchanged input reproduces the same
identity; any bound-field change produces a different one, which
``coordinator.py``'s conflicting-replay handling (135Q §29) governs.
"""

from __future__ import annotations

from typing import Optional

from pcae.cltr.digest import compute_dict_digest

REHEARSAL_STAGE = "stage_2_atomic_publication_rehearsal"
PRODUCTION_AUTHORITY_DISCLOSURE = "legacy"


def compute_rehearsal_generation_id(
    *,
    migration_epoch: str,
    authority_epoch: str,
    transition_id: str,
    shared_input_package_id: str,
    final_input_revision_digest: str,
    phase_id: str,
    task_id: Optional[str],
    schema_versions: dict,
) -> str:
    return compute_dict_digest(
        {
            "migration_epoch": migration_epoch,
            "authority_epoch": authority_epoch,
            "transition_id": transition_id,
            "shared_input_package_id": shared_input_package_id,
            "final_input_revision_digest": final_input_revision_digest,
            "phase_id": phase_id,
            "task_id": task_id,
            "schema_versions": schema_versions,
            "rehearsal_stage": REHEARSAL_STAGE,
            "production_authority_disclosure": PRODUCTION_AUTHORITY_DISCLOSURE,
        }
    )


ROLLBACK_STAGE = "stage_2_rollback_rehearsal"


def compute_rollback_request_id(
    *,
    phase_id: str,
    transition_id: str,
    migration_epoch: str,
    authority_epoch: str,
    source_rehearsal_generation_id: Optional[str],
    target_rehearsal_generation_id: str,
    reason: str,
) -> str:
    """135U -- deterministic rollback-request identity, frozen from 135Q
    §33/§36's exactly-once binding ("rollback rehearsal (per-rollback-
    target idempotency, §36)"). Never random/timestamp-derived; stable
    across processes, working directories, hash seeds, environment
    ordering, locale, temporary roots, and filesystem timestamps because
    it is a pure function of these bound, verified fields only. Changes
    if -- and only if -- one of these contract-bound inputs changes,
    which is exactly the conflicting-replay detection surface (135U
    phase brief §8)."""

    return compute_dict_digest(
        {
            "phase_id": phase_id,
            "transition_id": transition_id,
            "migration_epoch": migration_epoch,
            "authority_epoch": authority_epoch,
            "source_rehearsal_generation_id": source_rehearsal_generation_id,
            "target_rehearsal_generation_id": target_rehearsal_generation_id,
            "reason": reason,
            "rollback_stage": ROLLBACK_STAGE,
            "production_authority_disclosure": PRODUCTION_AUTHORITY_DISCLOSURE,
        }
    )
