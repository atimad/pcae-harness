"""Read-only Stage 1 migration reconciliation (phase brief §29).

Inspects persisted migration evidence for one ``phase_id`` and reports;
never creates or enriches input, never reruns derivations, never repairs
files, never replays comparison, never publishes pointers, never
promotes reports, never dispatches notification, never creates a marker
or receipt, never changes migration stage, never grants authority.
"""

from __future__ import annotations

import json
from pathlib import Path

from pcae.cltr.migration.persistence import DEFAULT_MIGRATION_ROOT

NON_AUTHORITY_DISCLOSURE = {
    "migration_evidence_only": True,
    "authoritative": False,
    "mutation": "none",
    "runtime_boundary": "observe",
}


def _find_transitions_for_phase(migration_root: Path, phase_id: str) -> list[dict]:
    epochs_dir = migration_root / "epochs"
    matches: list[dict] = []
    if not epochs_dir.exists():
        return matches
    for epoch_dir in sorted(p for p in epochs_dir.iterdir() if p.is_dir()):
        transitions_dir = epoch_dir / "transitions"
        if not transitions_dir.exists():
            continue
        for transition_dir_ in sorted(p for p in transitions_dir.iterdir() if p.is_dir()):
            evidence_path = transition_dir_ / "evidence" / "evidence.json"
            if not evidence_path.exists():
                continue
            try:
                evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            input_path = transition_dir_ / "inputs" / "1.json"
            observed_phase_id = None
            if input_path.exists():
                try:
                    first_revision = json.loads(input_path.read_text(encoding="utf-8"))
                    observed_phase_id = first_revision.get("fields", {}).get("phase_id")
                except (json.JSONDecodeError, OSError):
                    pass
            if observed_phase_id == phase_id:
                matches.append({"evidence": evidence, "directory": str(transition_dir_)})
    return matches


def _read_failures(directory: str) -> list[dict]:
    failures_dir = Path(directory) / "failures"
    if not failures_dir.exists():
        return []
    out = []
    for path in sorted(failures_dir.iterdir()):
        try:
            out.append(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    return out


def reconcile(phase_id: str, migration_root: Path = DEFAULT_MIGRATION_ROOT) -> dict:
    matches = _find_transitions_for_phase(Path(migration_root), phase_id)
    if not matches:
        return {
            "phase_id": phase_id,
            "found": False,
            "blockers": ["no migration evidence exists for this phase_id"],
            **NON_AUTHORITY_DISCLOSURE,
        }

    transitions = []
    blockers: list[str] = []
    for match in matches:
        evidence = match["evidence"]
        failures = _read_failures(match["directory"])
        if failures:
            blockers.append(f"transition {evidence.get('transition_id')} has {len(failures)} recorded failure(s)")
        if not evidence.get("migration_progression_eligible"):
            blockers.append(f"transition {evidence.get('transition_id')} is not migration-progression-eligible")
        transitions.append(
            {
                "transition_id": evidence.get("transition_id"),
                "migration_epoch": evidence.get("migration_epoch"),
                "authority_epoch": evidence.get("authority_epoch"),
                "production_authority": evidence.get("production_authority"),
                "comparison_overall_class": evidence.get("comparison_overall_class"),
                "migration_progression_eligible": evidence.get("migration_progression_eligible"),
                "evidence_digest": evidence.get("evidence_digest"),
                "failures": len(failures),
            }
        )

    return {
        "phase_id": phase_id,
        "found": True,
        "transitions": transitions,
        "blockers": blockers,
        **NON_AUTHORITY_DISCLOSURE,
    }
