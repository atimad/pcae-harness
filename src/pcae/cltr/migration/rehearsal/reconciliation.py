"""Read-only Stage 2 rehearsal reconciliation (135Q §35).

Inspects persisted rehearsal evidence for one ``phase_id``; never
creates, finalizes, publishes, repairs, replays, dispatches, or mutates
anything. Modeled directly on
``pcae.cltr.migration.reconciliation.reconcile``'s existing precedent.
"""

from __future__ import annotations

from pathlib import Path

from pcae.cltr.migration.disclosure import NON_AUTHORITY_DISCLOSURE
from pcae.cltr.migration.rehearsal.persistence import DEFAULT_MIGRATION_ROOT, generations_dir, read_json
from pcae.cltr.migration.rehearsal.recovery import classify, current_pointer_generation_id, list_transition_ids
from pcae.cltr.migration.rehearsal.rollback import list_rollback_evidence


def _find_rehearsal_transitions_for_phase(migration_root: Path, phase_id: str) -> list[dict]:
    epochs_dir = migration_root / "epochs"
    matches: list[dict] = []
    if not epochs_dir.exists():
        return matches
    for epoch_dir in sorted(p for p in epochs_dir.iterdir() if p.is_dir()):
        migration_epoch = epoch_dir.name
        for transition_id in list_transition_ids(migration_root, migration_epoch):
            generation_id = current_pointer_generation_id(migration_root, migration_epoch, transition_id)
            if generation_id is None:
                continue
            generation = generations_dir(migration_root, migration_epoch, transition_id, generation_id)
            manifest = read_json(generation / "manifest.json")
            if manifest is None:
                continue
            evidence = read_json(generation / "rehearsal_evidence.json")
            observed_phase_id = None
            for entry in manifest.get("artifact_inventory", []):
                if entry.get("artifact_kind") == "repository_transition_candidate":
                    artifact = read_json(generation / entry["path"])
                    if artifact:
                        observed_phase_id = artifact.get("phase_id")
            if observed_phase_id != phase_id:
                # 135U -- a rollback may have moved the current-rehearsal
                # pointer to a generation finalized under a *different*
                # phase_id than the one that requested the rollback. The
                # rollback's own evidence records the requesting phase_id
                # explicitly, so a phase_id that authored a rollback for
                # this transition must still resolve here (never silently
                # lost from status/reconcile just because the pointer no
                # longer points at "its own" generation).
                rollback_phase_ids = {
                    record.get("phase_id") for record in list_rollback_evidence(migration_root, migration_epoch, transition_id)
                }
                if phase_id not in rollback_phase_ids:
                    continue
            matches.append(
                {
                    "migration_epoch": migration_epoch,
                    "transition_id": transition_id,
                    "rehearsal_generation_id": generation_id,
                    "manifest": manifest,
                    "evidence": evidence,
                }
            )
    return matches


def reconcile(phase_id: str, migration_root: Path = DEFAULT_MIGRATION_ROOT) -> dict:
    matches = _find_rehearsal_transitions_for_phase(Path(migration_root), phase_id)
    if not matches:
        return {
            "phase_id": phase_id,
            "found": False,
            "blockers": ["no rehearsal evidence exists for this phase_id"],
            **NON_AUTHORITY_DISCLOSURE,
        }

    transitions = []
    blockers: list[str] = []
    for match in matches:
        recovery_state = classify(
            Path(migration_root), match["migration_epoch"], match["transition_id"], match["rehearsal_generation_id"]
        )
        evidence = match["evidence"] or {}
        if not evidence.get("progression_eligibility"):
            blockers.append(f"transition {match['transition_id']} is not rehearsal-progression-eligible")
        rollback_history = list_rollback_evidence(Path(migration_root), match["migration_epoch"], match["transition_id"])
        transitions.append(
            {
                "transition_id": match["transition_id"],
                "migration_epoch": match["migration_epoch"],
                "rehearsal_generation_id": match["rehearsal_generation_id"],
                "generation_digest": match["manifest"].get("generation_digest"),
                "verification_status": match["manifest"].get("verification_status"),
                "outcome": evidence.get("outcome"),
                "progression_eligibility": evidence.get("progression_eligibility", False),
                "recovery_state": recovery_state.value,
                "rollback_history": rollback_history,
            }
        )

    return {
        "phase_id": phase_id,
        "found": True,
        "transitions": transitions,
        "blockers": blockers,
        **NON_AUTHORITY_DISCLOSURE,
    }
