"""Read-only Stage 1 migration status aggregation (phase brief §28).

Strictly read-only: never creates, enriches, replays, or repairs
anything. ``mutation: "none"`` on every returned payload.
"""

from __future__ import annotations

import json
from pathlib import Path

from pcae.cltr.migration.configuration import MigrationConfigurationError, load_configuration
from pcae.cltr.migration.enums import ComparisonResultClass
from pcae.cltr.migration.persistence import DEFAULT_MIGRATION_ROOT

NON_AUTHORITY_DISCLOSURE = {
    "migration_evidence_only": True,
    "authoritative": False,
    "mutation": "none",
    "runtime_boundary": "observe",
}


def _iter_evidence_files(migration_root: Path):
    epochs_dir = migration_root / "epochs"
    if not epochs_dir.exists():
        return
    for epoch_dir in sorted(p for p in epochs_dir.iterdir() if p.is_dir()):
        transitions_dir = epoch_dir / "transitions"
        if not transitions_dir.exists():
            continue
        for transition_dir_ in sorted(p for p in transitions_dir.iterdir() if p.is_dir()):
            evidence_path = transition_dir_ / "evidence" / "evidence.json"
            if evidence_path.exists():
                try:
                    yield json.loads(evidence_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    continue


def migration_status(migration_root: Path = DEFAULT_MIGRATION_ROOT) -> dict:
    try:
        config = load_configuration()
        config_error = None
    except MigrationConfigurationError as exc:
        config = None
        config_error = str(exc)

    evidence_records = list(_iter_evidence_files(Path(migration_root)))
    comparison_counts: dict[str, int] = {}
    authority_relevant_mismatch_count = 0
    unverifiable_count = 0
    for record in evidence_records:
        overall = record.get("comparison_overall_class")
        comparison_counts[overall] = comparison_counts.get(overall, 0) + 1
        if overall in {c.value for c in ComparisonResultClass} and overall not in (
            ComparisonResultClass.EXACT_MATCH.value,
            ComparisonResultClass.SEMANTIC_MATCH.value,
        ):
            if overall == ComparisonResultClass.UNVERIFIABLE.value:
                unverifiable_count += 1
            else:
                authority_relevant_mismatch_count += 1

    blockers = []
    if config_error:
        blockers.append(f"migration configuration invalid: {config_error}")

    return {
        "dual_derivation_enabled": bool(config and config.dual_derivation_enabled),
        "migration_stage": config.migration_stage.value if config else None,
        "production_authority": "legacy",
        "migration_epoch": config.migration_epoch if config else None,
        "authority_epoch": None,
        "shadow_enabled": bool(config and config.shadow_enabled),
        "transition_evidence_count": len(evidence_records),
        "comparison_counts_by_class": comparison_counts,
        "authority_relevant_mismatch_count": authority_relevant_mismatch_count,
        "unverifiable_count": unverifiable_count,
        "migration_progression_eligible_count": sum(
            1 for r in evidence_records if r.get("migration_progression_eligible")
        ),
        "blockers": blockers,
        "limitations": (
            ["configuration invalid; dual derivation is treated as inactive"] if config_error else []
        ),
        **NON_AUTHORITY_DISCLOSURE,
    }
