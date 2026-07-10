"""Historical Memory validation (127D pipeline stage 10, implicit within stages 3-9).

Independently re-checks the assembled Historical Memory Snapshot
against the required invariants (127B Section 6, 127D Section 9)
rather than trusting the builder's own construction. Fails closed on
any violation.
"""

from __future__ import annotations

import re
from typing import Any

from pcae.repository_intelligence.historical_memory.historical_builder import (
    HistoricalGenerationError,
)

_EVENT_TYPES = frozenset(
    {
        "phase_started",
        "phase_completed",
        "architecture_defined",
        "architecture_reviewed",
        "contract_frozen",
        "contract_verified",
        "schema_implemented",
        "schema_verified",
        "prototype_added",
        "integration_recorded",
        "hardening_completed",
        "repair_completed",
        "release_published",
        "governance_check_completed",
        "report_generated",
        "metadata_promoted",
        "notification_sent",
        "decision_recorded",
        "supersession_recorded",
        "correction_recorded",
        "unknown",
    }
)

_RELATIONSHIP_TYPES = frozenset(
    {
        "introduced_by",
        "changed_by",
        "froze_contract",
        "verified_by",
        "repaired_by",
        "hardened_by",
        "supersedes",
        "corrects",
        "included_in_release",
        "documents",
        "related_to",
        "unknown",
    }
)

_REQUIRED_TOP_LEVEL_FIELDS = (
    "envelope",
    "snapshot_identity",
    "snapshot_subject",
    "snapshot_scope",
    "historical_window",
    "historical_events",
    "historical_claims",
    "historical_sources",
    "phase_lineage",
    "release_lineage",
    "decision_history",
    "repair_hardening_history",
    "supersession_correction_history",
    "historical_relationships",
    "unknowns_gaps",
    "snapshot_limitations",
    "boundary_disclosures",
    "disclaimers",
    "historical_memory_snapshot_disclaimer",
)


def validate_historical_snapshot(historical: dict[str, Any]) -> None:
    """Validate ``historical`` against every 127D Section 9 requirement.

    Raises ``HistoricalGenerationError`` (fail closed) on the first
    violation found. Does not mutate ``historical``.
    """
    _validate_top_level_fields_present(historical)
    _validate_unique_event_identifiers(historical["historical_events"])
    _validate_unique_claim_identifiers(historical["historical_claims"])
    _validate_unique_phase_identifiers(historical["phase_lineage"])
    _validate_unique_relationship_identifiers(historical["historical_relationships"])
    _validate_event_types(historical["historical_events"])
    _validate_relationship_types(historical["historical_relationships"])
    reference_ids = _collect_reference_ids(historical)
    _validate_relationship_endpoints(historical["historical_relationships"], reference_ids)
    _validate_deterministic_ordering(historical)
    _validate_provenance_completeness(historical)
    _validate_limitation_completeness(historical)
    _validate_boundary_completeness(historical)


def _validate_top_level_fields_present(historical: dict[str, Any]) -> None:
    missing = [field for field in _REQUIRED_TOP_LEVEL_FIELDS if field not in historical]
    if missing:
        raise HistoricalGenerationError(f"historical snapshot is missing required fields: {missing}")


def _validate_unique_event_identifiers(events: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    for event in events:
        event_id = event["event_id"]
        if event_id in seen:
            raise HistoricalGenerationError(f"duplicate event_id detected: {event_id!r}")
        seen.add(event_id)


def _validate_unique_claim_identifiers(claims: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    for claim in claims:
        claim_id = claim["claim_id"]
        if claim_id in seen:
            raise HistoricalGenerationError(f"duplicate claim_id detected: {claim_id!r}")
        seen.add(claim_id)


def _validate_unique_phase_identifiers(phase_lineage: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    for record in phase_lineage:
        phase_id = record["phase_id"]
        if phase_id in seen:
            raise HistoricalGenerationError(f"duplicate phase_id detected: {phase_id!r}")
        seen.add(phase_id)


def _validate_unique_relationship_identifiers(relationships: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    for rel in relationships:
        rel_id = rel["relationship_id"]
        if rel_id in seen:
            raise HistoricalGenerationError(f"duplicate relationship_id detected: {rel_id!r}")
        seen.add(rel_id)


def _validate_event_types(events: list[dict[str, Any]]) -> None:
    for event in events:
        if event["event_type"] not in _EVENT_TYPES:
            raise HistoricalGenerationError(
                f"event {event['event_id']!r} has invalid event_type {event['event_type']!r}"
            )


def _validate_relationship_types(relationships: list[dict[str, Any]]) -> None:
    for rel in relationships:
        if rel["relationship_type"] not in _RELATIONSHIP_TYPES:
            raise HistoricalGenerationError(
                f"relationship {rel['relationship_id']!r} has invalid "
                f"relationship_type {rel['relationship_type']!r}"
            )


def _collect_reference_ids(historical: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for record in historical["phase_lineage"]:
        ids.add(f"ref:phase:{_safe(record['phase_id'])}")
    for record in historical["repair_hardening_history"]:
        ids.add(record["record_id"])
    return ids


def _safe(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "-", value)


def _validate_relationship_endpoints(relationships: list[dict[str, Any]], reference_ids: set[str]) -> None:
    for rel in relationships:
        source_id = rel["source_reference"]["reference_id"]
        target_id = rel["target_reference"]["reference_id"]
        if source_id not in reference_ids:
            raise HistoricalGenerationError(
                f"relationship {rel['relationship_id']!r} references unknown "
                f"source_reference {source_id!r}"
            )
        if target_id not in reference_ids:
            raise HistoricalGenerationError(
                f"relationship {rel['relationship_id']!r} references unknown "
                f"target_reference {target_id!r}"
            )


def _validate_deterministic_ordering(historical: dict[str, Any]) -> None:
    event_ids = [e["event_id"] for e in historical["historical_events"]]
    if event_ids != sorted(event_ids):
        raise HistoricalGenerationError("historical_events are not deterministically ordered by event_id")
    claim_ids = [c["claim_id"] for c in historical["historical_claims"]]
    if claim_ids != sorted(claim_ids):
        raise HistoricalGenerationError("historical_claims are not deterministically ordered by claim_id")
    phase_ids = [p["phase_id"] for p in historical["phase_lineage"]]
    if phase_ids != sorted(phase_ids):
        raise HistoricalGenerationError("phase_lineage is not deterministically ordered by phase_id")
    rel_ids = [r["relationship_id"] for r in historical["historical_relationships"]]
    if rel_ids != sorted(rel_ids):
        raise HistoricalGenerationError(
            "historical_relationships are not deterministically ordered by relationship_id"
        )


def _validate_provenance_completeness(historical: dict[str, Any]) -> None:
    collections = (
        (historical["historical_events"], "event", "event_id"),
        (historical["historical_claims"], "claim", "claim_id"),
        (historical["phase_lineage"], "phase_lineage", "phase_id"),
        (historical["repair_hardening_history"], "repair_hardening", "record_id"),
        (historical["historical_relationships"], "relationship", "relationship_id"),
    )
    for collection, label, id_field in collections:
        for item in collection:
            if not item.get("source_attribution"):
                raise HistoricalGenerationError(
                    f"{label} {item[id_field]!r} is missing required source_attribution"
                )


def _validate_limitation_completeness(historical: dict[str, Any]) -> None:
    collections = (
        (historical["historical_events"], "event", "event_id"),
        (historical["historical_claims"], "claim", "claim_id"),
        (historical["phase_lineage"], "phase_lineage", "phase_id"),
        (historical["repair_hardening_history"], "repair_hardening", "record_id"),
        (historical["historical_relationships"], "relationship", "relationship_id"),
    )
    for collection, label, id_field in collections:
        for item in collection:
            if not item.get("limitations"):
                raise HistoricalGenerationError(
                    f"{label} {item[id_field]!r} is missing required limitations"
                )
    if not historical.get("snapshot_limitations"):
        raise HistoricalGenerationError("historical snapshot is missing required snapshot_limitations")


def _validate_boundary_completeness(historical: dict[str, Any]) -> None:
    if not historical.get("boundary_disclosures"):
        raise HistoricalGenerationError("historical snapshot is missing required boundary_disclosures")
    if not historical.get("disclaimers"):
        raise HistoricalGenerationError("historical snapshot is missing required disclaimers")
    if not historical.get("historical_memory_snapshot_disclaimer"):
        raise HistoricalGenerationError(
            "historical snapshot is missing required historical_memory_snapshot_disclaimer"
        )
