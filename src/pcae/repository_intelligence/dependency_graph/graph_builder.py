"""Dependency Knowledge Graph deterministic construction (126D pipeline stages 1-9).

Consumes exactly one existing Repository Knowledge Snapshot artifact,
reached exclusively through the Track 121 Query Layer
(``pcae.repository_intelligence.query``). Never reads the snapshot
file directly, never rescans the repository, never reruns the Track
120 generator.

The ``entity_type`` -> ``node_type`` and containment -> ``related_to``
mappings implemented here are exactly the mappings frozen in 126B
Sections 4.3/5.2 and grounded against the real Track 120 generator in
126D Section 2/5.1/5.2. No relationship is created without direct,
deterministic support in the source snapshot; class/function-level
nodes and import/depends_on edges remain unimplemented per 126B's own
v1 scope decision (Repository Knowledge Snapshot does not yet extract
that content).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pcae.repository_intelligence.attribution import (
    commit_attribution,
    limitation_record,
    verification_state,
)
from pcae.repository_intelligence.consumer_validation import (
    ensure_boundary_material_present,
    ensure_limitations_present,
    ensure_records_have_attribution,
    validate_query_result_shape,
)
from pcae.repository_intelligence.query.query_engine import (
    QueryExecutionError,
    execute_query,
)
from pcae.repository_intelligence.query.query_request import QueryRequest
from pcae.repository_intelligence.query.query_result import QueryResult
from pcae.repository_intelligence.query.snapshot_loader import (
    SnapshotCompatibilityError,
    SnapshotLoadError,
    load_snapshot,
)

ARTIFACT_CONTRACT_VERSION = "119E.1.0"
SCHEMA_CONCEPT_VERSION = "119C.1.0-concept"
ENVELOPE_EXECUTABLE_SCHEMA_VERSION = "119K.1.0-json-schema"
GRAPH_EXECUTABLE_SCHEMA_VERSION = "119S.1.0-json-schema"

DEPENDENCY_KNOWLEDGE_GRAPH_SNAPSHOT_DISCLAIMER = (
    "This Dependency Knowledge Graph Snapshot describes a declared, "
    "source-attributed relationship view of the repository. It does "
    "not construct or query a graph, does not prove dependency truth "
    "or completeness, is not Repository State, and does not authorize "
    "action or execution."
)

READ_ONLY_BOUNDARY = (
    "This artifact is descriptive and read-only. It does not mutate "
    "repository state, lifecycle state, or any other PCAE subsystem "
    "state."
)
DECISION_BOUNDARY = (
    "This artifact is not a decision. Decision Evaluation is the sole "
    "decision maker in PCAE. This artifact provides context only."
)
EXECUTION_BOUNDARY = (
    "This artifact does not execute commands, invoke runtimes, "
    "mediate shells, route execution, or authorize execution. "
    "Execution remains unavailable."
)

DISCLAIMERS = {
    "non_decision_disclaimer": (
        "This artifact is not a decision. Decision Evaluation remains "
        "required for PCAE decisions."
    ),
    "no_execution_disclaimer": (
        "This artifact does not execute commands, invoke runtimes, "
        "mediate shells, route execution, or authorize execution. "
        "Execution remains unavailable."
    ),
    "advisory_non_authority_disclaimer": (
        "This artifact may inform Advisory context but does not "
        "convert Advisory output into approval, permission, "
        "enforcement, or execution."
    ),
    "evidence_boundary_disclaimer": (
        "This artifact may link to Evidence but does not replace, "
        "bypass, or preempt the Evidence subsystem."
    ),
    "repository_state_boundary_disclaimer": (
        "This artifact may describe repository context but does not "
        "replace Repository State."
    ),
}

BOUNDARY_DISCLOSURES = {
    "read_only": True,
    "no_execution": True,
    "non_decision": True,
    "advisory_non_authority": True,
    "decision_evaluation_required": True,
    "no_repository_mutation": True,
    "no_lifecycle_mutation": True,
    "no_evidence_replacement": True,
    "no_repository_state_replacement": True,
}

# 126B Section 4.3 / 126D Section 5.1: RKS entity_type -> DKG node_type.
# Frozen; do not add, rename, or reinterpret values here without a
# governed contract-amendment phase.
_ENTITY_TYPE_TO_NODE_TYPE = {
    "document": "document",
    "schema": "schema",
    "package": "package",
    "module": "module",
    "command": "command",
    "configuration": "configuration",
    "test": "test",
    "task": "task",
    "phase": "phase",
    "release": "release",
    "runtime_component": "runtime_component",
    "advisory_component": "advisory_component",
    "evidence_artifact": "evidence_artifact",
    "repository_skill": "repository_skill",
    "contract": "contract",
    "report": "evidence_artifact",
    "source_file": "file",
    "unknown": "unknown",
}

# RKS verification_state.state_value -> DKG node_status. node_status's
# closed vocabulary does not include "verified"; "known" is the
# closest honest mapping (126D grounding).
_STATE_VALUE_TO_NODE_STATUS = {
    "verified": "known",
    "partially_verified": "partially_verified",
    "unverified": "unverified",
    "unknown": "unknown",
    "stale": "superseded",
    "conflicting": "conflicting",
}

CONTAINMENT_EDGE_TYPE = "related_to"
CONTAINMENT_LIMITATION = limitation_record(
    limitation_type="scope_limitation",
    limitation_description=(
        "This edge represents declared path containment (repository "
        "contains a top-level entity), mapped to the frozen "
        "'related_to' edge type per 126B Section 5.2. True "
        "hierarchical containment semantics are not distinguished "
        "from other 'related_to' relationships at v1."
    ),
)
IMPORTS_LIMITATION_TEXT = (
    "This graph declares zero 'imports'/'depends_on'-derived edges "
    "because the source Repository Knowledge Snapshot generator "
    "(Track 120) does not parse file contents, imports, or symbols. "
    "This is an inherited Track 120 limitation, not a Dependency "
    "Knowledge Graph deficiency; it will resolve automatically once a "
    "future, separately governed Track 120 enhancement declares "
    "import/dependency relationships."
)
CLASS_FUNCTION_LIMITATION_TEXT = (
    "This graph does not model class- or function-level nodes. "
    "Repository Knowledge Snapshot does not currently extract "
    "class/function-level entities, so no source-attributed basis "
    "exists for such nodes at v1, per 126B Section 4.3."
)


class GraphGenerationError(RuntimeError):
    """Raised when the Dependency Knowledge Graph Builder must fail closed."""


def _node_status_for(state_value: str) -> str:
    return _STATE_VALUE_TO_NODE_STATUS.get(state_value, "unknown")


def _repository_node_id() -> str:
    return "node:repository"


def _node_id_for_entity(entity_path: str) -> str:
    return f"node:{entity_path}"


def _edge_id(edge_type: str, source_node_id: str, target_node_id: str) -> str:
    return f"edge:{edge_type}:{source_node_id}->{target_node_id}"


def _load_and_validate_entity_ids(snapshot_path: Path) -> tuple[dict[str, Any], list[str]]:
    try:
        raw_snapshot = load_snapshot(snapshot_path)
    except (SnapshotLoadError, SnapshotCompatibilityError) as exc:
        raise GraphGenerationError(str(exc)) from exc

    entities = raw_snapshot.get("architectural_entities", [])
    entity_ids = [
        entity["entity_id"] for entity in entities if isinstance(entity, dict) and entity.get("entity_id")
    ]
    if not entity_ids:
        raise GraphGenerationError(
            "source Repository Knowledge Snapshot declares no "
            "architectural entities; refusing to produce a "
            "non-conformant graph with an empty required nodes array "
            "beyond the synthesized repository root."
        )
    return raw_snapshot, sorted(entity_ids)


def _query_entity(snapshot_path: Path, entity_id: str) -> QueryResult:
    request = QueryRequest(category="entity_lookup", target=entity_id)
    try:
        result = execute_query(snapshot_path, request)
    except QueryExecutionError as exc:
        raise GraphGenerationError(str(exc)) from exc

    validate_query_result_shape(
        result,
        required_fields=(
            "query_metadata",
            "source_artifact",
            "records",
            "attribution",
            "limitations",
            "unknowns",
            "boundary_disclosures",
            "disclaimers",
            "result_status",
        ),
        error_type=GraphGenerationError,
    )
    if result.result_status != "ok" or not result.records:
        raise GraphGenerationError(
            f"Query Layer returned no entity record for declared entity {entity_id!r}; "
            "refusing to synthesize a node without direct Query Layer support."
        )
    return result


def _query_snapshot_material(snapshot_path: Path) -> tuple[QueryResult, QueryResult]:
    try:
        limitations_result = execute_query(
            snapshot_path, QueryRequest(category="limitation_lookup")
        )
        boundary_result = execute_query(
            snapshot_path, QueryRequest(category="boundary_lookup")
        )
    except QueryExecutionError as exc:
        raise GraphGenerationError(str(exc)) from exc

    for result in (limitations_result, boundary_result):
        validate_query_result_shape(
            result,
            required_fields=(
                "query_metadata",
                "source_artifact",
                "records",
                "attribution",
                "limitations",
                "boundary_disclosures",
                "disclaimers",
                "result_status",
            ),
            error_type=GraphGenerationError,
        )

    try:
        ensure_limitations_present(
            limitations_result.limitations, error_type=GraphGenerationError
        )
        ensure_boundary_material_present(
            boundary_result.boundary_disclosures,
            boundary_result.disclaimers,
            error_type=GraphGenerationError,
        )
    except GraphGenerationError:
        raise

    return limitations_result, boundary_result


def _build_nodes_and_claims(
    snapshot_path: Path,
    entity_ids: list[str],
    commit_sha: str,
    repository_name: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    nodes: list[dict[str, Any]] = []
    claims: list[dict[str, Any]] = []
    all_attribution: list[dict[str, Any]] = []

    repository_node_id = _repository_node_id()
    repository_source_attribution = [
        commit_attribution(source_id="source:repository-root", commit_sha=commit_sha)
    ]
    nodes.append(
        {
            "node_id": repository_node_id,
            "node_type": "repository",
            "node_name": repository_name,
            "node_status": "known",
            "source_attribution": repository_source_attribution,
            "verification_state": verification_state(
                state_value="known",
                state_reason=(
                    "Repository identity synthesized once per graph from "
                    "the source Repository Knowledge Snapshot envelope's "
                    "own repository_context, not from an individual "
                    "architectural entity record."
                ),
                commit_sha=commit_sha,
                state_limitations=[
                    "Synthesized root node; not itself an "
                    "architectural_entities record."
                ],
            ),
            "limitations": [
                limitation_record(
                    limitation_type="scope_limitation",
                    limitation_description=(
                        "This is a synthesized repository-root node, "
                        "one per graph, deterministically derived from "
                        "the source snapshot's repository identity."
                    ),
                )
            ],
        }
    )
    claims.append(
        {
            "claim_id": f"claim:node-existence:{repository_node_id}",
            "claim_type": "node_existence",
            "claim_subject": repository_node_id,
            "claim_statement": (
                f"A repository-root node exists for {repository_name!r} "
                f"at commit {commit_sha}."
            ),
            "source_attribution": repository_source_attribution,
            "verification_state": verification_state(
                state_value="known",
                state_reason="Derived deterministically from snapshot envelope repository_context.",
                commit_sha=commit_sha,
                state_limitations=["Limited to repository identity declared in the source snapshot."],
            ),
            "limitations": [
                limitation_record(
                    limitation_type="scope_limitation",
                    limitation_description="One synthesized repository-root node per graph.",
                )
            ],
        }
    )
    all_attribution.extend(repository_source_attribution)

    for entity_id in entity_ids:
        result = _query_entity(snapshot_path, entity_id)
        record = result.records[0]
        entity_type = record.get("entity_type", "unknown")
        entity_path = record.get("entity_path") or entity_id
        node_type = _ENTITY_TYPE_TO_NODE_TYPE.get(entity_type, "unknown")
        node_id = _node_id_for_entity(entity_path)
        record_verification = record.get("verification_state") or {}
        state_value = record_verification.get("state_value", "unknown")
        node_status = _node_status_for(state_value)
        source_attribution = record.get("source_attribution") or list(result.attribution)

        try:
            ensure_records_have_attribution(
                has_content=True,
                attribution=source_attribution,
                error_type=GraphGenerationError,
                message=f"entity {entity_id!r} has no source attribution; refusing to create a node.",
            )
        except GraphGenerationError:
            raise

        node_limitations = record.get("limitations") or list(result.limitations)
        if not node_limitations:
            raise GraphGenerationError(
                f"entity {entity_id!r} has no limitation records; refusing to create a node."
            )

        nodes.append(
            {
                "node_id": node_id,
                "node_type": node_type,
                "node_name": record.get("entity_name", entity_id),
                "node_status": node_status,
                "source_attribution": source_attribution,
                "verification_state": record_verification
                or verification_state(
                    state_value="unknown",
                    state_reason="Source entity did not declare a verification_state.",
                    commit_sha=commit_sha,
                    state_limitations=["No verification_state was present on the source entity."],
                ),
                "limitations": node_limitations,
            }
        )
        claims.append(
            {
                "claim_id": f"claim:node-existence:{node_id}",
                "claim_type": "node_existence",
                "claim_subject": node_id,
                "claim_statement": (
                    f"A node exists for entity {entity_id!r} "
                    f"(type {entity_type!r}) declared in the source "
                    "Repository Knowledge Snapshot."
                ),
                "source_attribution": source_attribution,
                "verification_state": record_verification
                or verification_state(
                    state_value="unknown",
                    state_reason="Source entity did not declare a verification_state.",
                    commit_sha=commit_sha,
                    state_limitations=["No verification_state was present on the source entity."],
                ),
                "limitations": node_limitations,
            }
        )
        all_attribution.extend(source_attribution)

    return nodes, claims, all_attribution


def _build_containment_edges(
    nodes: list[dict[str, Any]], commit_sha: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    edges: list[dict[str, Any]] = []
    claims: list[dict[str, Any]] = []
    all_attribution: list[dict[str, Any]] = []

    repository_node_id = _repository_node_id()
    for node in nodes:
        if node["node_id"] == repository_node_id:
            continue
        edge_id = _edge_id(CONTAINMENT_EDGE_TYPE, repository_node_id, node["node_id"])
        source_attribution = list(node["source_attribution"])
        edges.append(
            {
                "edge_id": edge_id,
                "edge_type": CONTAINMENT_EDGE_TYPE,
                "source_node_id": repository_node_id,
                "target_node_id": node["node_id"],
                "direction": "directed",
                "relationship_status": "declared",
                "source_attribution": source_attribution,
                "verification_state": node["verification_state"],
                "limitations": [CONTAINMENT_LIMITATION] + list(node["limitations"]),
            }
        )
        claims.append(
            {
                "claim_id": f"claim:edge-existence:{edge_id}",
                "claim_type": "edge_existence",
                "claim_subject": edge_id,
                "claim_statement": (
                    f"The repository declares containment of "
                    f"{node['node_id']!r}, mapped to the frozen "
                    "'related_to' edge type per 126B Section 5.2."
                ),
                "source_node_reference": repository_node_id,
                "target_node_reference": node["node_id"],
                "source_attribution": source_attribution,
                "verification_state": node["verification_state"],
                "limitations": [CONTAINMENT_LIMITATION],
            }
        )
        all_attribution.extend(source_attribution)

    return edges, claims, all_attribution


def build_graph_content(snapshot_path: Path, *, generated_at_utc: str) -> dict[str, Any]:
    """Build a schema-conformant Dependency Knowledge Graph Snapshot.

    Deterministic given a fixed source Repository Knowledge Snapshot,
    except ``generated_at_utc``/``snapshot_created_at_utc`` (approved
    non-substantive metadata, mirroring 120B Section 6's rule for
    Repository Knowledge Snapshot).

    Consumes the source snapshot exclusively through the Track 121
    Query Layer (``pcae.repository_intelligence.query``); never reads
    the snapshot file directly, never rescans the repository, never
    reruns the Track 120 generator.

    Raises ``GraphGenerationError`` (fail-closed, 126B Section 12 /
    126D Section 10) if the source snapshot is invalid, unsupported,
    or missing required provenance/limitation/boundary material.
    """
    raw_snapshot, entity_ids = _load_and_validate_entity_ids(snapshot_path)
    limitations_result, boundary_result = _query_snapshot_material(snapshot_path)

    envelope = raw_snapshot.get("envelope") or {}
    repository_context = envelope.get("repository_context") or {}
    commit_sha = repository_context.get("repository_commit")
    if not commit_sha:
        raise GraphGenerationError(
            "source Repository Knowledge Snapshot envelope is missing "
            "repository_context.repository_commit; refusing to "
            "produce a graph without a stable commit anchor."
        )
    repository_identity = repository_context.get("repository_identity") or {}
    repository_name = repository_identity.get("identity_value") or "unknown-repository"
    snapshot_id = (raw_snapshot.get("snapshot_identity") or {}).get("snapshot_id", "unknown-snapshot")
    source_executable_schema_version = (raw_snapshot.get("snapshot_identity") or {}).get(
        "executable_schema_version"
    )

    nodes, node_claims, node_attribution = _build_nodes_and_claims(
        snapshot_path, entity_ids, commit_sha, repository_name
    )
    edges, edge_claims, edge_attribution = _build_containment_edges(nodes, commit_sha)
    claims = node_claims + edge_claims

    if not nodes:
        raise GraphGenerationError(
            "no nodes could be constructed; refusing to produce a "
            "non-conformant graph with an empty required nodes array."
        )
    if not claims:
        raise GraphGenerationError(
            "no dependency claims could be constructed; refusing to "
            "produce a non-conformant graph with an empty required "
            "dependency_claims array."
        )

    dependency_sources = _merge_unique_attribution(
        node_attribution + edge_attribution + list(limitations_result.attribution)
    )
    if not dependency_sources:
        raise GraphGenerationError(
            "no source attribution could be assembled for this graph; "
            "refusing to produce a non-conformant artifact."
        )

    snapshot_limitations = _merge_unique_limitations(
        list(limitations_result.limitations)
        + [
            limitation_record(
                limitation_type="scope_limitation",
                limitation_description=IMPORTS_LIMITATION_TEXT,
            ),
            limitation_record(
                limitation_type="scope_limitation",
                limitation_description=CLASS_FUNCTION_LIMITATION_TEXT,
            ),
        ]
    )

    unknowns_gaps = [
        {
            "unknown_id": "unknown:imports-depends-on",
            "unknown_subject": "import and dependency relationships",
            "missing_node_or_edge": "depends_on edges derived from import statements",
            "affected_scope": "graph-wide",
            "uncertainty_state": verification_state(
                state_value="unknown",
                state_reason=(
                    "Repository Knowledge Snapshot does not parse file "
                    "contents, imports, or symbols."
                ),
                commit_sha=commit_sha,
                state_limitations=[IMPORTS_LIMITATION_TEXT],
            ),
            "limitation": limitation_record(
                limitation_type="scope_limitation",
                limitation_description=IMPORTS_LIMITATION_TEXT,
            ),
        },
        {
            "unknown_id": "unknown:class-function-nodes",
            "unknown_subject": "class- and function-level entities",
            "missing_node_or_edge": "class and function nodes",
            "affected_scope": "graph-wide",
            "uncertainty_state": verification_state(
                state_value="unknown",
                state_reason=(
                    "Repository Knowledge Snapshot does not extract "
                    "class- or function-level entities."
                ),
                commit_sha=commit_sha,
                state_limitations=[CLASS_FUNCTION_LIMITATION_TEXT],
            ),
            "limitation": limitation_record(
                limitation_type="scope_limitation",
                limitation_description=CLASS_FUNCTION_LIMITATION_TEXT,
            ),
        },
    ]

    boundary_disclosures = dict(boundary_result.boundary_disclosures) or dict(BOUNDARY_DISCLOSURES)
    disclaimers = dict(boundary_result.disclaimers) or dict(DISCLAIMERS)

    graph_id = f"dkg-{commit_sha}"
    graph_name = f"Dependency Knowledge Graph for {repository_name}"
    graph_scope = (
        f"Structural relationships derived from Repository Knowledge "
        f"Snapshot {snapshot_id!r}. v1 covers path-containment "
        "relationships between the repository root and Track 120's "
        "declared top-level entities only; import/dependency "
        "relationships and class/function-level nodes are not yet "
        "available (see unknowns_gaps)."
    )
    graph_generation_method_disclosure = (
        "Generated deterministically by "
        "pcae.repository_intelligence.dependency_graph.graph_builder "
        "(Phase 126E prototype) by translating each declared "
        "Repository Knowledge Snapshot architectural entity into a "
        "node via the frozen entity_type -> node_type mapping (126B "
        "Section 4.3 / 126D Section 5.1), and declaring one "
        "repository-to-entity containment edge per node via the "
        "frozen contains -> related_to mapping (126B Section 5.2). No "
        "graph was traversed, queried, or reasoned over by this "
        "generator; only declared Repository Knowledge Snapshot "
        "content, reached exclusively through the Track 121 Query "
        "Layer, was translated."
    )

    graph_metadata = {
        "graph_id": graph_id,
        "graph_name": graph_name,
        "graph_kind": "dependency",
        "graph_scope": graph_scope,
        "graph_directionality": "directed",
        "graph_completeness_state": "partial",
        "graph_generation_method_disclosure": graph_generation_method_disclosure,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "source_attribution": dependency_sources,
        "verification_state": verification_state(
            state_value="partially_verified",
            state_reason=(
                "Nodes and containment edges are directly derived from "
                "declared snapshot content; import/dependency "
                "relationships and class/function nodes remain unknown."
            ),
            commit_sha=commit_sha,
            state_limitations=[IMPORTS_LIMITATION_TEXT, CLASS_FUNCTION_LIMITATION_TEXT],
        ),
        "limitations": snapshot_limitations,
    }

    envelope_source_attribution = list(dependency_sources)
    graph_envelope = {
        "artifact_id": f"dependency_knowledge_graph_snapshot:{commit_sha}",
        "artifact_type": "dependency_knowledge_graph_snapshot",
        "artifact_family": "dependency_knowledge_graph_snapshot",
        "artifact_contract_version": ARTIFACT_CONTRACT_VERSION,
        "schema_concept_version": SCHEMA_CONCEPT_VERSION,
        "executable_schema_version": ENVELOPE_EXECUTABLE_SCHEMA_VERSION,
        "repository_context": dict(repository_context),
        "generated_at_utc": generated_at_utc,
        "producer": {
            "producer_type": "tool",
            "producer_identity": (
                "pcae repository-intelligence dependency-graph generate "
                "(Phase 126E read-only prototype)"
            ),
        },
        "source_attribution": envelope_source_attribution,
        "evidence_links": [
            {
                "evidence_id": "evidence-gap:envelope",
                "evidence_type": "evidence_gap_marker",
                "evidence_source": {
                    "source_type": "none",
                    "source_identity": "not_applicable",
                },
                "supported_claim": {
                    "claim_id": "envelope",
                    "claim_summary": (
                        "No Evidence subsystem link is established by "
                        "this prototype."
                    ),
                },
                "support_strength": "inconclusive",
                "candidate_or_accepted_state": "unsubmitted",
                "decision_evaluation_eligibility": "not_eligible_evidence_gap",
                "limitations": [
                    "This prototype does not integrate with the "
                    "Evidence subsystem."
                ],
            }
        ],
        "verification_state": "partially_verified",
        "uncertainty_state": "partially_verified",
        "conflict_state": "none",
        "supersession_state": "current",
        "read_only_boundary": READ_ONLY_BOUNDARY,
        "decision_boundary": DECISION_BOUNDARY,
        "execution_boundary": EXECUTION_BOUNDARY,
        "boundary_disclosures": dict(boundary_disclosures),
        "limitations": [
            limitation_record(
                limitation_type="scope_limitation",
                limitation_description=(
                    "This is a narrow, first-prototype Dependency "
                    "Knowledge Graph; see snapshot_limitations for the "
                    "full disclosure."
                ),
            )
        ],
        "disclaimers": dict(disclaimers),
    }

    graph: dict[str, Any] = {
        "envelope": graph_envelope,
        "snapshot_identity": {
            "snapshot_id": graph_id,
            "snapshot_subject": graph_name,
            "snapshot_scope": graph_scope,
            "graph_scope": graph_scope,
            "snapshot_created_at_utc": generated_at_utc,
            "artifact_contract_version": ARTIFACT_CONTRACT_VERSION,
            "schema_concept_version": SCHEMA_CONCEPT_VERSION,
            "executable_schema_version": GRAPH_EXECUTABLE_SCHEMA_VERSION,
        },
        "snapshot_subject": graph_name,
        "snapshot_scope": graph_scope,
        "graph_metadata": graph_metadata,
        "nodes": sorted(nodes, key=lambda item: item["node_id"]),
        "edges": sorted(edges, key=lambda item: item["edge_id"]),
        "dependency_claims": sorted(claims, key=lambda item: item["claim_id"]),
        "dependency_sources": dependency_sources,
        "evidence_links": [],
        "dependency_paths": [],
        "graph_views": [],
        "clusters": [],
        "external_references": [],
        "unknowns_gaps": unknowns_gaps,
        "snapshot_limitations": snapshot_limitations,
        "conflict_or_supersession_records": [],
        "derivation_records": [],
        "boundary_disclosures": dict(boundary_disclosures),
        "disclaimers": dict(disclaimers),
        "dependency_knowledge_graph_snapshot_disclaimer": DEPENDENCY_KNOWLEDGE_GRAPH_SNAPSHOT_DISCLAIMER,
    }

    if source_executable_schema_version is None:
        raise GraphGenerationError(
            "source Repository Knowledge Snapshot is missing its own "
            "executable_schema_version; refusing to derive a graph "
            "from an unversioned source artifact."
        )

    return graph


def _merge_unique_attribution(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[str, dict[str, Any]] = {}
    for item in items:
        source_id = item.get("source_id")
        if source_id is None:
            continue
        unique[source_id] = item
    return [unique[key] for key in sorted(unique)]


def _merge_unique_limitations(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[tuple[Any, ...], dict[str, Any]] = {}
    for item in items:
        key = (item.get("limitation_type"), item.get("limitation_description"))
        unique[key] = item
    return [unique[key] for key in sorted(unique, key=lambda k: (k[0] or "", k[1] or ""))]
