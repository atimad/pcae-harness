"""Stage 2 recovery-state classification (135Q §27).

Read-only: classifies the current on-disk state for one transition from
recorded evidence alone -- never from titles, Git history, or "latest
file present" heuristics. Used by ``status.py``/``reconciliation.py`` to
report state truthfully; this implementation does not itself perform
automated resumption of an interrupted candidate (disclosed limitation,
see ``docs/PHASE_135_ATOMIC_PUBLICATION_REHEARSAL_IMPLEMENTATION.md``) --
an abandoned ``candidates/<id>/`` directory is detected and reported as
``candidate_incomplete``/quarantine-eligible on inspection, per 135Q
§26's "quarantined on next inspection if abandoned" rows, rather than
silently repaired or blindly retried.
"""

from __future__ import annotations

from pathlib import Path

from pcae.cltr.migration.rehearsal.enums import RecoveryState
from pcae.cltr.migration.rehearsal.persistence import (
    candidates_dir,
    generations_dir,
    pointer_path,
    quarantine_dir,
    read_json,
)


def classify(migration_root: Path, migration_epoch: str, transition_id: str, rehearsal_generation_id: str) -> RecoveryState:
    quarantine = quarantine_dir(migration_root, migration_epoch, transition_id, rehearsal_generation_id)
    if quarantine.exists() and (quarantine / "quarantine_record.json").exists():
        return RecoveryState.QUARANTINE_REQUIRED

    generation = generations_dir(migration_root, migration_epoch, transition_id, rehearsal_generation_id)
    manifest = read_json(generation / "manifest.json")
    if manifest is not None:
        pointer = read_json(pointer_path(migration_root, migration_epoch, transition_id))
        if pointer is not None and pointer.get("rehearsal_generation_id") == rehearsal_generation_id:
            evidence = read_json(generation / "rehearsal_evidence.json")
            return RecoveryState.POINTER_PUBLISHED if evidence is not None else RecoveryState.RESULT_RECORD_INCOMPLETE
        return RecoveryState.GENERATION_FINALIZED_UNPUBLISHED

    candidate = candidates_dir(migration_root, migration_epoch, transition_id, rehearsal_generation_id)
    if candidate.exists():
        manifest_path = candidate / "manifest.json"
        if manifest_path.exists():
            return RecoveryState.CANDIDATE_COMPLETE_UNVERIFIED
        if any(candidate.iterdir()):
            return RecoveryState.CANDIDATE_INCOMPLETE
    return RecoveryState.NO_CANDIDATE


def current_pointer_generation_id(migration_root: Path, migration_epoch: str, transition_id: str) -> str | None:
    pointer = read_json(pointer_path(migration_root, migration_epoch, transition_id))
    if pointer is None:
        return None
    return pointer.get("rehearsal_generation_id")


def list_transition_ids(migration_root: Path, migration_epoch: str) -> list[str]:
    rehearsals_dir = migration_root / "epochs" / migration_epoch / "rehearsals"
    if not rehearsals_dir.exists():
        return []
    return sorted(p.name for p in rehearsals_dir.iterdir() if p.is_dir())
