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
