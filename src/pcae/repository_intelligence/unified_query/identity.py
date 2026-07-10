"""Identity resolution, reusing Track 130's already-proven pattern exactly (131D Section 9).

This module introduces no new identity-derivation logic of its own: it
imports and calls Track 130's existing, tested
``_node_id_for_entity`` for Dependency Knowledge Graph node
identifiers, and applies plain exact dict-key lookups for every other
family's own already-existing stable identifier fields (131C Section
10's field inventory). No alias table, no fuzzy/heuristic/
probabilistic matching, no silent merges anywhere in this module.
"""

from __future__ import annotations

from typing import Any

# Reused directly from Track 130, not reimplemented -- the same import
# pattern integration_builder.py itself already establishes as
# acceptable cross-module reuse within this package family.
from pcae.repository_intelligence.dependency_graph.graph_builder import (
    _node_id_for_entity as node_id_for_entity,
)

# Each covered family's own already-existing stable identifier
# field(s), confirmed via direct schema inspection (131C Section 10).
# Order matters: the first matching field wins for a given record.
FAMILY_ID_FIELDS: dict[str, tuple[str, ...]] = {
    "repository_knowledge_snapshot": ("entity_id", "capability_id", "contract_id"),
    "dependency_knowledge_graph": ("node_id", "edge_id"),
    "historical_memory": ("event_id", "claim_id", "record_id"),
    "change_impact": ("entity_id",),
    # Independently confirmed during 131E's own implementation: the
    # real Advisory Context Builder's `selected_repository_intelligence`
    # entries are raw Repository Knowledge Snapshot records passed
    # through unchanged (see `advisory_context_builder.py`'s own
    # `selected_records = all_records`), not a `context_item_id`-keyed
    # shape as `advisory_intelligence_context_package.schema.json`
    # nominally declares -- the same class of schema/reality drift
    # independently found for Change Impact (module docstring,
    # `artifact_loading.load_advisory_context`).
    "advisory_context": ("entity_id", "capability_id", "contract_id"),
    "cross_artifact_integration": ("context_id", "entity_id"),
}


def find_by_id(records: list[dict[str, Any]], id_fields: tuple[str, ...], target: str) -> dict[str, Any] | None:
    """Exact-match lookup only. Returns None (never a best guess) on miss."""
    for record in records:
        if not isinstance(record, dict):
            continue
        for field_name in id_fields:
            if record.get(field_name) == target:
                return record
    return None


def unresolved_identity_record(*, target: str, reason: str) -> dict[str, Any]:
    """Explicit unresolved-identity record, matching Track 130's own shape.

    Mirrors ``integration_builder.py``'s ``unresolved_identities`` entry
    shape (``entity_id``/``uncertainty_state``/``unresolved_reason``)
    exactly -- a miss is recorded as data, never silently omitted and
    never resolved by a fuzzy/heuristic/probabilistic guess.
    """
    return {
        "entity_id": target,
        "uncertainty_state": "unresolved",
        "unresolved_reason": reason,
    }
