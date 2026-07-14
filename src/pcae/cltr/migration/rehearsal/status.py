"""Read-only Stage 2 rehearsal status aggregation (135Q §34).

Strictly read-only: never derives, finalizes, publishes, repairs, or
replays anything. Modeled directly on
``pcae.cltr.migration.status.migration_status``'s existing precedent.
"""

from __future__ import annotations

from pathlib import Path

from pcae.cltr.migration.disclosure import NON_AUTHORITY_DISCLOSURE
from pcae.cltr.migration.rehearsal.configuration import RehearsalConfigurationError, load_rehearsal_configuration
from pcae.cltr.migration.rehearsal.persistence import DEFAULT_MIGRATION_ROOT, pointer_path, read_json
from pcae.cltr.migration.rehearsal.recovery import current_pointer_generation_id, list_transition_ids


def rehearsal_status(migration_root: Path = DEFAULT_MIGRATION_ROOT) -> dict:
    try:
        config = load_rehearsal_configuration()
        config_error = None
    except RehearsalConfigurationError as exc:
        config = None
        config_error = str(exc)

    blockers = []
    if config_error:
        blockers.append(f"rehearsal configuration invalid: {config_error}")

    transitions_summary: list[dict] = []
    if config is not None and config.stage1.migration_epoch:
        for transition_id in list_transition_ids(migration_root, config.stage1.migration_epoch):
            generation_id = current_pointer_generation_id(migration_root, config.stage1.migration_epoch, transition_id)
            pointer = read_json(pointer_path(migration_root, config.stage1.migration_epoch, transition_id))
            transitions_summary.append(
                {
                    "transition_id": transition_id,
                    "current_rehearsal_generation_id": generation_id,
                    "pointer_valid": pointer is not None,
                    "generation_digest": pointer.get("generation_digest") if pointer else None,
                }
            )

    return {
        "atomic_rehearsal_enabled": bool(config and config.atomic_rehearsal_enabled),
        "production_authority": "legacy",
        "migration_epoch": config.stage1.migration_epoch if config else None,
        "authority_epoch": None,
        "transitions": transitions_summary,
        "blockers": blockers,
        "limitations": (
            ["configuration invalid; atomic rehearsal is treated as inactive"] if config_error else []
        )
        + [
            "status reports rehearsal-namespace state only; it never reflects, "
            "gates, or determines production lifecycle truth",
        ],
        **NON_AUTHORITY_DISCLOSURE,
    }
