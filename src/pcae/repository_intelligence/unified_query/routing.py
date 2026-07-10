"""Deterministic routing over declared artifact responsibilities (131B Section 7 / 131D Section 4).

A fixed, declared category -> artifact-family mapping. No heuristics,
no fuzzy routing, no ranking, no optimization, no indexing -- a plain
dict lookup, matching ``query.query_request.SUPPORTED_QUERY_CATEGORIES``'s
own existing ``frozenset`` dispatch pattern exactly.

Every multi-family category must be explicitly enumerated in
``MULTI_FAMILY_CATEGORIES`` -- a fixed allow-list maintained
independently of ``ROUTING_TABLE`` itself (131D Section 4's own "no
category may be discovered to be multi-family at implementation time"
requirement). A category resolving to more than one family that is
*not* also present in this independent allow-list raises
``RoutingAmbiguityError`` rather than being handled ad hoc -- this is
what makes the allow-list a real, enforced gate rather than a
tautology derived from the table it is meant to gate.
"""

from __future__ import annotations

from pcae.repository_intelligence.unified_query.errors import (
    RoutingAmbiguityError,
    UnsupportedQueryCategoryError,
)

REPOSITORY_KNOWLEDGE_SNAPSHOT = "repository_knowledge_snapshot"
DEPENDENCY_KNOWLEDGE_GRAPH = "dependency_knowledge_graph"
HISTORICAL_MEMORY = "historical_memory"
CHANGE_IMPACT = "change_impact"
ADVISORY_CONTEXT = "advisory_context"
CROSS_ARTIFACT_INTEGRATION = "cross_artifact_integration"

SIX_ARTIFACT_FAMILIES = (
    REPOSITORY_KNOWLEDGE_SNAPSHOT,
    DEPENDENCY_KNOWLEDGE_GRAPH,
    HISTORICAL_MEMORY,
    CHANGE_IMPACT,
    ADVISORY_CONTEXT,
    CROSS_ARTIFACT_INTEGRATION,
)

# One single-family category per covered artifact family (131D Section
# 2.5's completion criterion: at least one query per covered family),
# plus the one explicitly-enumerated multi-family category.
ROUTING_TABLE: dict[str, tuple[str, ...]] = {
    "rks_entity_lookup": (REPOSITORY_KNOWLEDGE_SNAPSHOT,),
    "dependency_node_lookup": (DEPENDENCY_KNOWLEDGE_GRAPH,),
    "historical_event_lookup": (HISTORICAL_MEMORY,),
    "change_impact_entity_lookup": (CHANGE_IMPACT,),
    "advisory_context_item_lookup": (ADVISORY_CONTEXT,),
    "cross_artifact_reference_lookup": (CROSS_ARTIFACT_INTEGRATION,),
    # The one explicitly-enumerated multi-family category (131B Section
    # 12 / 131D Section 4): resolves a Change Impact entity's
    # corresponding Dependency Knowledge Graph node via Track 130's
    # already-built integration package -- never independently
    # re-derived. All three families are declared as required: the
    # relationship itself is read from the Cross-Artifact Integration
    # package (already computed by Track 130), not re-derived from
    # Change Impact/Dependency Knowledge Graph content directly.
    "change_impact_to_dependency_node": (
        CHANGE_IMPACT,
        DEPENDENCY_KNOWLEDGE_GRAPH,
        CROSS_ARTIFACT_INTEGRATION,
    ),
}

# Independent, hand-maintained allow-list -- deliberately NOT derived
# from ROUTING_TABLE. A category must appear in both this set and
# ROUTING_TABLE (with >1 family) to be treated as a valid multi-family
# route; a table entry with >1 family that is absent here is an
# undeclared ambiguity and fails closed (this is what makes the
# RoutingAmbiguityError path real and testable, not tautological).
MULTI_FAMILY_CATEGORIES: frozenset[str] = frozenset({"change_impact_to_dependency_node"})


def route(category: str, *, table: dict[str, tuple[str, ...]] | None = None) -> tuple[str, ...]:
    """Resolve a query category to its declared artifact family/families.

    ``table`` is injectable (defaulting to the frozen ``ROUTING_TABLE``)
    so tests can exercise the ``RoutingAmbiguityError`` path directly
    with a synthetic table entry that is multi-family but absent from
    the real, independent ``MULTI_FAMILY_CATEGORIES`` allow-list.
    """
    routing_table = ROUTING_TABLE if table is None else table
    if category not in routing_table:
        raise UnsupportedQueryCategoryError(f"unsupported query category: {category!r}")
    families = routing_table[category]
    if len(families) > 1 and category not in MULTI_FAMILY_CATEGORIES:
        raise RoutingAmbiguityError(
            f"category {category!r} resolves to multiple families "
            f"{families!r} but is not declared in the explicit "
            "multi-family allow-list"
        )
    return families
