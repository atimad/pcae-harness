"""Dependency Knowledge Graph validation (126D pipeline stage 10).

Independently re-checks the assembled graph against the required
invariants (126B Section 6, 126D Section 8) rather than trusting the
builder's own construction. Fails closed on any violation.
"""

from __future__ import annotations

from typing import Any

from pcae.repository_intelligence.dependency_graph.graph_builder import (
    GraphGenerationError,
)

_VALID_NODE_TYPES = frozenset(
    {
        "repository",
        "package",
        "module",
        "file",
        "document",
        "schema",
        "command",
        "configuration",
        "test",
        "task",
        "phase",
        "release",
        "runtime_component",
        "advisory_component",
        "evidence_artifact",
        "repository_skill",
        "contract",
        "unknown",
    }
)

_VALID_EDGE_TYPES = frozenset(
    {
        "depends_on",
        "references",
        "documents",
        "tests",
        "configures",
        "governs",
        "produces",
        "consumes",
        "verifies",
        "supersedes",
        "related_to",
        "derived_from",
        "unknown",
    }
)

_REQUIRED_METADATA_FIELDS = (
    "graph_id",
    "graph_name",
    "graph_kind",
    "graph_scope",
    "graph_directionality",
    "graph_completeness_state",
    "graph_generation_method_disclosure",
    "source_attribution",
    "verification_state",
    "limitations",
)


def validate_graph(graph: dict[str, Any]) -> None:
    """Validate ``graph`` against every 126D Section 8 requirement.

    Raises ``GraphGenerationError`` (fail closed) on the first
    violation found. Does not mutate ``graph``.
    """
    _validate_unique_node_identifiers(graph["nodes"])
    _validate_unique_edge_identifiers(graph["edges"])
    node_ids = {node["node_id"] for node in graph["nodes"]}
    _validate_edge_endpoints(graph["edges"], node_ids)
    _validate_node_categories(graph["nodes"])
    _validate_edge_categories(graph["edges"])
    _validate_deterministic_ordering(graph["nodes"], graph["edges"])
    _validate_metadata_completeness(graph["graph_metadata"])
    _validate_provenance_completeness(graph["nodes"], graph["edges"], graph["dependency_claims"])
    _validate_limitation_completeness(graph["nodes"], graph["edges"], graph["dependency_claims"], graph)
    _validate_boundary_completeness(graph)


def _validate_unique_node_identifiers(nodes: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    for node in nodes:
        node_id = node["node_id"]
        if node_id in seen:
            raise GraphGenerationError(f"duplicate node_id detected: {node_id!r}")
        seen.add(node_id)


def _validate_unique_edge_identifiers(edges: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    for edge in edges:
        edge_id = edge["edge_id"]
        if edge_id in seen:
            raise GraphGenerationError(f"duplicate edge_id detected: {edge_id!r}")
        seen.add(edge_id)


def _validate_edge_endpoints(edges: list[dict[str, Any]], node_ids: set[str]) -> None:
    for edge in edges:
        if edge["source_node_id"] not in node_ids:
            raise GraphGenerationError(
                f"edge {edge['edge_id']!r} references unknown source_node_id "
                f"{edge['source_node_id']!r}"
            )
        if edge["target_node_id"] not in node_ids:
            raise GraphGenerationError(
                f"edge {edge['edge_id']!r} references unknown target_node_id "
                f"{edge['target_node_id']!r}"
            )


def _validate_node_categories(nodes: list[dict[str, Any]]) -> None:
    for node in nodes:
        if node["node_type"] not in _VALID_NODE_TYPES:
            raise GraphGenerationError(
                f"node {node['node_id']!r} has invalid node_type {node['node_type']!r}"
            )


def _validate_edge_categories(edges: list[dict[str, Any]]) -> None:
    for edge in edges:
        if edge["edge_type"] not in _VALID_EDGE_TYPES:
            raise GraphGenerationError(
                f"edge {edge['edge_id']!r} has invalid edge_type {edge['edge_type']!r}"
            )


def _validate_deterministic_ordering(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> None:
    node_ids = [node["node_id"] for node in nodes]
    if node_ids != sorted(node_ids):
        raise GraphGenerationError("nodes are not deterministically ordered by node_id")
    edge_ids = [edge["edge_id"] for edge in edges]
    if edge_ids != sorted(edge_ids):
        raise GraphGenerationError("edges are not deterministically ordered by edge_id")


def _validate_metadata_completeness(graph_metadata: dict[str, Any]) -> None:
    missing = [field for field in _REQUIRED_METADATA_FIELDS if not graph_metadata.get(field)]
    # node_count/edge_count may legitimately be 0; only check presence, not truthiness, for those.
    for count_field in ("node_count", "edge_count"):
        if count_field not in graph_metadata:
            missing.append(count_field)
    if missing:
        raise GraphGenerationError(f"graph_metadata is missing required fields: {missing}")


def _validate_provenance_completeness(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    claims: list[dict[str, Any]],
) -> None:
    for collection, label in ((nodes, "node"), (edges, "edge"), (claims, "dependency_claim")):
        for item in collection:
            identifier = item.get("node_id") or item.get("edge_id") or item.get("claim_id")
            if not item.get("source_attribution"):
                raise GraphGenerationError(
                    f"{label} {identifier!r} is missing required source_attribution"
                )


def _validate_limitation_completeness(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    graph: dict[str, Any],
) -> None:
    for collection, label in ((nodes, "node"), (edges, "edge"), (claims, "dependency_claim")):
        for item in collection:
            identifier = item.get("node_id") or item.get("edge_id") or item.get("claim_id")
            if not item.get("limitations"):
                raise GraphGenerationError(
                    f"{label} {identifier!r} is missing required limitations"
                )
    if not graph.get("snapshot_limitations"):
        raise GraphGenerationError("graph is missing required snapshot_limitations")


def _validate_boundary_completeness(graph: dict[str, Any]) -> None:
    if not graph.get("boundary_disclosures"):
        raise GraphGenerationError("graph is missing required boundary_disclosures")
    if not graph.get("disclaimers"):
        raise GraphGenerationError("graph is missing required disclaimers")
    if not graph.get("dependency_knowledge_graph_snapshot_disclaimer"):
        raise GraphGenerationError(
            "graph is missing required dependency_knowledge_graph_snapshot_disclaimer"
        )
