from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from pcae.core.agent import (
    _CRI_KNOWN_PHASES,
    _IRG_STRATEGIC_REVIEW_REGISTRY,
    _SRG_BRANCH_REGISTRY,
    _SRG_OBJECTIVE_REGISTRY,
)
from pcae.core.paths import HarnessPath
from pcae.core.provenance import read_provenance_history


STRATEGIC_LINEAGE_RELATIVE_PATH = Path(".pcae") / "strategic-lineage.json"

STRATEGIC_LINEAGE_ADVISORY = (
    "Strategic lineage is append-only, human-approved decision evidence. "
    "It does not own roadmap, phase, branch, review, capability mapping, or "
    "architecture state. Validation and display are read-only; execution_allowed=False."
)

DECISION_BASIS_VALUES = frozenset(
    {
        "strategic_review",
        "coherence_failure",
        "roadmap_gap",
        "human_override",
        "risk_mitigation",
        "technical_debt",
        "architecture_requirement",
    }
)

LINEAGE_STATUS_VALUES = frozenset({"approved", "rejected", "deferred", "superseded"})
ACTIVATION_VALIDATION_STATUS_VALUES = frozenset(
    {"validated", "migration_exempt", "invalid"}
)
ALTERNATIVE_DISPOSITION_VALUES = frozenset({"rejected", "deferred"})
# Explicitly reviewed migration exemptions only. Never derive exemptions from
# mutable roadmap lifecycle state.
PRE_65J_MIGRATION_EXEMPT_PHASE_IDS = frozenset({"65I"})

REQUIRED_LINEAGE_FIELDS = (
    "lineage_id",
    "lineage_timestamp",
    "lineage_status",
    "decided_by",
    "decision_basis",
    "source_phase_id",
    "predecessor_phase_id",
    "activated_phase_id",
    "selected_branch_id",
    "objective_ids",
    "rationale",
    "review_ids",
    "finding_snapshot_hash",
    "recommendation",
    "considered_alternatives",
    "rejected_alternatives",
    "deferred_alternatives",
    "roadmap_debt",
    "supersedes_lineage_id",
    "human_approved",
    "execution_allowed",
    "activation_event_id",
    "activation_validation_status",
)


@dataclass(frozen=True)
class StrategicLineageValidation:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    record_count: int
    active_phase_id: str
    current_lineage_id: str | None
    migration_exempt_phase_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "active_phase_id": self.active_phase_id,
            "current_lineage_id": self.current_lineage_id,
            "errors": list(self.errors),
            "migration_exempt_phase_ids": list(self.migration_exempt_phase_ids),
            "record_count": self.record_count,
            "valid": self.valid,
            "warnings": list(self.warnings),
        }


def load_strategic_lineage_records(root: HarnessPath) -> tuple[dict[str, Any], ...]:
    target = root.join(STRATEGIC_LINEAGE_RELATIVE_PATH)
    if not target.is_file():
        return ()
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid strategic lineage JSON: {error.msg}.") from error
    if not isinstance(data, list):
        raise ValueError("Invalid strategic lineage registry: expected a list of records.")
    if not all(isinstance(record, dict) for record in data):
        raise ValueError("Invalid strategic lineage registry: every record must be an object.")
    return tuple(dict(record) for record in data)


def strategic_review_snapshot_hash(review_ids: list[str] | tuple[str, ...]) -> str:
    review_by_id = {
        record["review_id"]: record for record in _IRG_STRATEGIC_REVIEW_REGISTRY
    }
    selected = [review_by_id[review_id] for review_id in sorted(review_ids)]
    payload = json.dumps(
        selected,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def current_active_phase_id() -> str:
    active = [
        phase["phase_id"]
        for phase in _CRI_KNOWN_PHASES
        if phase.get("status") == "active"
    ]
    return active[0] if len(active) == 1 else ""


def current_strategic_lineage(
    root: HarnessPath,
    records: tuple[dict[str, Any], ...] | None = None,
) -> dict[str, Any] | None:
    registry = records if records is not None else load_strategic_lineage_records(root)
    superseded_ids = {
        record.get("supersedes_lineage_id")
        for record in registry
        if record.get("supersedes_lineage_id")
    }
    active_phase_id = current_active_phase_id()
    candidates = [
        record
        for record in registry
        if record.get("lineage_status") == "approved"
        and record.get("human_approved") is True
        and record.get("activated_phase_id") == active_phase_id
        and record.get("lineage_id") not in superseded_ids
    ]
    return dict(candidates[-1]) if len(candidates) == 1 else None


def validate_strategic_lineage(
    root: HarnessPath,
    records: tuple[dict[str, Any], ...] | None = None,
) -> StrategicLineageValidation:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        registry = records if records is not None else load_strategic_lineage_records(root)
    except ValueError as error:
        return StrategicLineageValidation(
            valid=False,
            errors=(str(error),),
            warnings=(),
            record_count=0,
            active_phase_id=current_active_phase_id(),
            current_lineage_id=None,
            migration_exempt_phase_ids=tuple(sorted(PRE_65J_MIGRATION_EXEMPT_PHASE_IDS)),
        )

    phase_by_id = {phase["phase_id"]: phase for phase in _CRI_KNOWN_PHASES}
    branch_by_id = {branch["branch_id"]: branch for branch in _SRG_BRANCH_REGISTRY}
    objective_ids = {objective["objective_id"] for objective in _SRG_OBJECTIVE_REGISTRY}
    review_by_id = {
        review["review_id"]: review for review in _IRG_STRATEGIC_REVIEW_REGISTRY
    }
    provenance_path = root.join(Path(".pcae") / "provenance-history.json")
    provenance_by_timestamp = {
        event.timestamp: event for event in read_provenance_history(root).events
    }

    lineage_ids = [str(record.get("lineage_id", "")) for record in registry]
    duplicate_ids = sorted(
        lineage_id
        for lineage_id in set(lineage_ids)
        if lineage_id and lineage_ids.count(lineage_id) > 1
    )
    for lineage_id in duplicate_ids:
        errors.append(f"Duplicate lineage_id: {lineage_id}.")

    known_lineage_ids = set(lineage_ids)
    superseded_targets: list[str] = []
    for index, record in enumerate(registry, start=1):
        lineage_id = str(record.get("lineage_id") or f"record-{index}")
        missing_fields = [
            field for field in REQUIRED_LINEAGE_FIELDS if field not in record
        ]
        if missing_fields:
            errors.append(
                f"{lineage_id}: missing required fields: {', '.join(missing_fields)}."
            )
            continue

        status = record["lineage_status"]
        if status not in LINEAGE_STATUS_VALUES:
            errors.append(f"{lineage_id}: invalid lineage_status {status!r}.")
        basis = record["decision_basis"]
        if basis not in DECISION_BASIS_VALUES:
            errors.append(f"{lineage_id}: invalid decision_basis {basis!r}.")
        if record["execution_allowed"] is not False:
            errors.append(f"{lineage_id}: execution_allowed must be False.")

        for field in ("source_phase_id", "predecessor_phase_id", "activated_phase_id"):
            phase_id = record[field]
            if phase_id and phase_id not in phase_by_id:
                errors.append(f"{lineage_id}: unknown {field} {phase_id!r}.")

        branch_id = record["selected_branch_id"]
        if branch_id not in branch_by_id:
            errors.append(f"{lineage_id}: unknown selected_branch_id {branch_id!r}.")

        unknown_objectives = sorted(set(record["objective_ids"]) - objective_ids)
        if unknown_objectives:
            errors.append(
                f"{lineage_id}: unknown objective_ids: {', '.join(unknown_objectives)}."
            )

        review_ids = record["review_ids"]
        unknown_reviews = sorted(set(review_ids) - set(review_by_id))
        if unknown_reviews:
            errors.append(
                f"{lineage_id}: unknown review_ids: {', '.join(unknown_reviews)}."
            )
        elif record["finding_snapshot_hash"] != strategic_review_snapshot_hash(review_ids):
            errors.append(f"{lineage_id}: finding_snapshot_hash does not match review authority.")

        alternatives = record["considered_alternatives"]
        if not isinstance(alternatives, list):
            errors.append(f"{lineage_id}: considered_alternatives must be a list.")
            alternatives = []
        alternative_phase_ids: set[str] = set()
        for alternative in alternatives:
            if not isinstance(alternative, dict):
                errors.append(f"{lineage_id}: every considered alternative must be an object.")
                continue
            missing = {
                "phase_id",
                "branch_id",
                "disposition",
                "reason",
            } - set(alternative)
            if missing:
                errors.append(
                    f"{lineage_id}: alternative missing fields: {', '.join(sorted(missing))}."
                )
                continue
            alternative_phase_id = alternative["phase_id"]
            alternative_phase_ids.add(alternative_phase_id)
            if alternative_phase_id not in phase_by_id:
                errors.append(
                    f"{lineage_id}: alternative references unknown phase {alternative_phase_id!r}."
                )
            if alternative["branch_id"] not in branch_by_id:
                errors.append(
                    f"{lineage_id}: alternative references unknown branch {alternative['branch_id']!r}."
                )
            if alternative["disposition"] not in ALTERNATIVE_DISPOSITION_VALUES:
                errors.append(
                    f"{lineage_id}: invalid alternative disposition {alternative['disposition']!r}."
                )
            if not str(alternative["reason"]).strip():
                errors.append(f"{lineage_id}: alternative reason must not be empty.")

        activated_phase_id = record["activated_phase_id"]
        if activated_phase_id in alternative_phase_ids:
            errors.append(
                f"{lineage_id}: activated phase cannot also be a considered alternative."
            )
        rejected_phase_ids = {
            alternative["phase_id"]
            for alternative in alternatives
            if isinstance(alternative, dict)
            and alternative.get("disposition") == "rejected"
        }
        deferred_phase_ids = {
            alternative["phase_id"]
            for alternative in alternatives
            if isinstance(alternative, dict)
            and alternative.get("disposition") == "deferred"
        }
        if set(record["rejected_alternatives"]) != rejected_phase_ids:
            errors.append(
                f"{lineage_id}: rejected_alternatives must enumerate only rejected alternative phase IDs."
            )
        if set(record["deferred_alternatives"]) != deferred_phase_ids:
            errors.append(
                f"{lineage_id}: deferred_alternatives must enumerate only deferred alternative phase IDs."
            )

        if status == "approved":
            if record["human_approved"] is not True:
                errors.append(
                    f"{lineage_id}: approved activation requires human_approved=True."
                )
            if not activated_phase_id:
                errors.append(
                    f"{lineage_id}: approved activation requires exactly one activated phase."
                )
            phase = phase_by_id.get(activated_phase_id)
            branch = branch_by_id.get(branch_id)
            if phase is not None and branch is not None:
                if phase["track_name"] != branch["branch_name"]:
                    errors.append(
                        f"{lineage_id}: selected branch does not match activated phase track."
                    )
                if branch["current_phase"] != activated_phase_id:
                    if activated_phase_id not in PRE_65J_MIGRATION_EXEMPT_PHASE_IDS:
                        errors.append(
                            f"{lineage_id}: activated phase does not match branch current_phase."
                        )
                    else:
                        warnings.append(
                            f"{lineage_id}: historical activation is covered by the pre-65J migration exemption."
                        )

        activation_status = record["activation_validation_status"]
        if activation_status not in ACTIVATION_VALIDATION_STATUS_VALUES:
            errors.append(
                f"{lineage_id}: invalid activation_validation_status {activation_status!r}."
            )
        elif activation_status == "validated":
            event_id = record["activation_event_id"]
            event = provenance_by_timestamp.get(event_id)
            if not event_id:
                errors.append(
                    f"{lineage_id}: validated activation requires activation_event_id."
                )
            elif not provenance_path.is_file():
                errors.append(
                    f"{lineage_id}: validated activation requires authoritative provenance history."
                )
            elif event is None:
                errors.append(f"{lineage_id}: activation_event_id does not exist in provenance.")
            elif event.event_type != "phase_activated":
                errors.append(
                    f"{lineage_id}: activation evidence must reference a phase_activated event."
                )
            elif activated_phase_id not in event.summary:
                errors.append(
                    f"{lineage_id}: activation evidence does not identify the activated phase."
                )
        elif activation_status == "migration_exempt":
            if activated_phase_id not in PRE_65J_MIGRATION_EXEMPT_PHASE_IDS:
                errors.append(
                    f"{lineage_id}: migration exemption is limited to pre-65J phases."
                )
            if record["activation_event_id"]:
                errors.append(
                    f"{lineage_id}: migration-exempt lineage must not claim activation_event_id."
                )

        supersedes_id = record["supersedes_lineage_id"]
        if supersedes_id:
            superseded_targets.append(supersedes_id)
            if supersedes_id not in known_lineage_ids:
                errors.append(
                    f"{lineage_id}: supersedes_lineage_id {supersedes_id!r} does not exist."
                )
            if supersedes_id == lineage_id:
                errors.append(f"{lineage_id}: a lineage record cannot supersede itself.")

    for target in sorted(set(superseded_targets)):
        if superseded_targets.count(target) > 1:
            errors.append(f"Lineage record {target} is superseded by multiple records.")

    active_phase_id = current_active_phase_id()
    current = current_strategic_lineage(root, registry)
    if active_phase_id and current is None:
        errors.append(
            f"Active phase {active_phase_id} requires exactly one approved, "
            "non-superseded strategic lineage record."
        )

    return StrategicLineageValidation(
        valid=not errors,
        errors=tuple(errors),
        warnings=tuple(warnings),
        record_count=len(registry),
        active_phase_id=active_phase_id,
        current_lineage_id=current["lineage_id"] if current is not None else None,
        migration_exempt_phase_ids=tuple(sorted(PRE_65J_MIGRATION_EXEMPT_PHASE_IDS)),
    )


def strategic_continuity_summary(root: HarnessPath) -> dict[str, Any]:
    records = load_strategic_lineage_records(root)
    current = current_strategic_lineage(root, records)
    validation = validate_strategic_lineage(root, records)
    if current is None:
        return {
            "available": False,
            "current": None,
            "deferred_alternatives": [],
            "rejected_alternatives": [],
            "referenced_review_findings": [],
            "validation": validation.to_dict(),
        }

    review_by_id = {
        review["review_id"]: review for review in _IRG_STRATEGIC_REVIEW_REGISTRY
    }
    referenced_findings = [
        {
            "review_id": review_id,
            "finding_count": len(review_by_id[review_id].get("findings", [])),
        }
        for review_id in current["review_ids"]
        if review_id in review_by_id
    ]
    return {
        "available": True,
        "current": current,
        "deferred_alternatives": [
            alternative
            for alternative in current["considered_alternatives"]
            if alternative["disposition"] == "deferred"
        ],
        "rejected_alternatives": [
            alternative
            for alternative in current["considered_alternatives"]
            if alternative["disposition"] == "rejected"
        ],
        "referenced_review_findings": referenced_findings,
        "validation": validation.to_dict(),
    }


def strategic_lineage_history(root: HarnessPath) -> dict[str, Any]:
    records = load_strategic_lineage_records(root)
    return {
        "record_count": len(records),
        "records": [dict(record) for record in records],
        "advisory": STRATEGIC_LINEAGE_ADVISORY,
    }
