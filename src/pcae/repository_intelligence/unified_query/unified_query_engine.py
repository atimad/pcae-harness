"""Unified Query lifecycle orchestration (131D Section 3): the nine stages, no additional ones.

1. Query request       -- ``UnifiedQueryRequest`` (caller-supplied).
2. Query normalization  -- ``request.normalize_request``.
3. Routing              -- ``routing.route``.
4. Artifact resolution  -- ``artifact_loading``.
5. Response assembly    -- this module's per-category handlers.
6. Provenance attachment -- ``provenance.build_provenance``.
7. Evidence preservation -- verbatim ``dict(record)`` copies only.
8. Boundary disclosure attachment -- ``boundary.unified_query_boundary_disclosures``.
9. Response delivery    -- deterministic serialization in ``UnifiedQueryResponse``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pcae.repository_intelligence.query.query_engine import evaluate_query as _evaluate_rks_query
from pcae.repository_intelligence.query.query_request import QueryRequest as _RksQueryRequest
from pcae.repository_intelligence.query.snapshot_loader import SnapshotLoadError
from pcae.repository_intelligence.unified_query import artifact_loading
from pcae.repository_intelligence.unified_query.boundary import (
    unified_query_boundary_disclosures,
    unified_query_boundary_notes,
)
from pcae.repository_intelligence.unified_query.errors import UnifiedQueryError
from pcae.repository_intelligence.unified_query.identity import (
    FAMILY_ID_FIELDS,
    find_by_id,
    unresolved_identity_record,
)
from pcae.repository_intelligence.unified_query.provenance import (
    DIRECT_DERIVATION_PATH,
    build_provenance,
)
from pcae.repository_intelligence.unified_query.request import (
    UnifiedQueryRequest,
    normalize_request,
)
from pcae.repository_intelligence.unified_query.response import UnifiedQueryResponse
from pcae.repository_intelligence.unified_query.routing import (
    ADVISORY_CONTEXT,
    CHANGE_IMPACT,
    CROSS_ARTIFACT_INTEGRATION,
    DEPENDENCY_KNOWLEDGE_GRAPH,
    HISTORICAL_MEMORY,
    REPOSITORY_KNOWLEDGE_SNAPSHOT,
    route,
)

RKS_SCHEMA_VERSION = "119O.1.0-json-schema"
DKG_SCHEMA_VERSION = "119S.1.0-json-schema"
HISTORICAL_MEMORY_SCHEMA_VERSION = "119Q.1.0-json-schema"


class MalformedRequestError(UnifiedQueryError):
    """Raised for a structurally invalid request (131D Section 8's reused ValueError-translation pattern)."""


def execute_unified_query(
    request: UnifiedQueryRequest,
    *,
    artifact_paths: dict[str, Path],
    repo_commit: str = "unknown",
) -> UnifiedQueryResponse:
    """Execute the full nine-stage Unified Query lifecycle.

    ``artifact_paths`` maps artifact family name (``routing.
    SIX_ARTIFACT_FAMILIES`` values) to the path of that family's
    already-generated artifact on disk. Only the families the routed
    category actually needs must be supplied.

    Never mutates any artifact, the repository, or runtime state.
    Every failure path raises an already-planned exception (131D
    Section 8) or produces an explicit uncertainty record -- never a
    silent omission, never an inferred recovery.
    """
    # Stage 1-2: request + normalization.
    try:
        metadata = normalize_request(request)
    except ValueError as exc:
        raise MalformedRequestError(str(exc)) from exc

    # Stage 3: routing.
    families = route(request.category)

    for family in families:
        if family not in artifact_paths:
            raise SnapshotLoadError(
                f"query category {request.category!r} requires artifact family "
                f"{family!r}, but no artifact path was supplied for it"
            )

    # Stage 4-8: artifact resolution, response assembly, provenance
    # attachment, evidence preservation, boundary disclosure
    # attachment -- all performed by the per-category handler.
    handler = _CATEGORY_HANDLERS[request.category]
    references, evidence, limitations, uncertainty = handler(request, artifact_paths, repo_commit)

    result_status = "ok" if references else ("unknown" if uncertainty else "ok")

    # Stage 9: response delivery -- deterministic serialization.
    return UnifiedQueryResponse(
        query_metadata=metadata,
        references=tuple(sorted(references, key=lambda r: r["originating_record"])),
        evidence=tuple(sorted(evidence, key=lambda e: e.get("record_id", ""))) if request.include_evidence else (),
        limitations=tuple(limitations),
        uncertainty=tuple(sorted(uncertainty, key=lambda u: u.get("entity_id", ""))),
        boundary_disclosures=unified_query_boundary_disclosures(),
        boundary_notes=tuple(unified_query_boundary_notes()),
        result_status=result_status,
    )


def _reference_and_evidence(
    *,
    record: dict[str, Any],
    record_id: str,
    family: str,
    source_locator_path: str,
    schema_version: str,
    derivation_path: str,
    include_evidence: bool,
    repo_commit: str,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    verification = record.get("verification_state") or record.get("uncertainty_state")
    if isinstance(verification, dict):
        verification = verification.get("state_value")
    provenance = build_provenance(
        authoritative_artifact=family,
        originating_record=record_id,
        source_locator_path=source_locator_path,
        schema_version=schema_version,
        derivation_path=derivation_path,
        record_verification_state=verification if isinstance(verification, str) else None,
        commit_sha=repo_commit,
    )
    reference = {"originating_record": record_id, "provenance": provenance}
    evidence_entry = {"record_id": record_id, "content": dict(record)} if include_evidence else None
    return reference, evidence_entry


def _handle_rks_entity_lookup(
    request: UnifiedQueryRequest, artifact_paths: dict[str, Path], repo_commit: str
) -> tuple[list, list, list, list]:
    path = artifact_paths[REPOSITORY_KNOWLEDGE_SNAPSHOT]
    snapshot = artifact_loading.load_repository_knowledge_snapshot(path)
    # Reuses Track 121's own query engine directly -- not reimplemented.
    result = _evaluate_rks_query(snapshot, _RksQueryRequest(category="entity_lookup", target=request.target))
    references: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    uncertainty: list[dict[str, Any]] = []
    for record in result.records:
        record_id = record.get("entity_id", "")
        reference, evidence_entry = _reference_and_evidence(
            record=record,
            record_id=record_id,
            family=REPOSITORY_KNOWLEDGE_SNAPSHOT,
            source_locator_path=str(path),
            schema_version=RKS_SCHEMA_VERSION,
            derivation_path=DIRECT_DERIVATION_PATH,
            include_evidence=request.include_evidence,
            repo_commit=repo_commit,
        )
        references.append(reference)
        if evidence_entry:
            evidence.append(evidence_entry)
    if not references:
        uncertainty.append(unresolved_identity_record(
            target=request.target or "",
            reason="No Repository Knowledge Snapshot entity matched the requested identifier.",
        ))
    limitations = list(result.limitations)
    return references, evidence, limitations, uncertainty


def _handle_dependency_node_lookup(
    request: UnifiedQueryRequest, artifact_paths: dict[str, Path], repo_commit: str
) -> tuple[list, list, list, list]:
    path = artifact_paths[DEPENDENCY_KNOWLEDGE_GRAPH]
    graph = artifact_loading.load_dependency_knowledge_graph(path)
    nodes = [n for n in graph.get("nodes", []) if isinstance(n, dict)]
    node = find_by_id(nodes, FAMILY_ID_FIELDS[DEPENDENCY_KNOWLEDGE_GRAPH], request.target or "")
    references: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    uncertainty: list[dict[str, Any]] = []
    if node is None:
        uncertainty.append(unresolved_identity_record(
            target=request.target or "",
            reason="No Dependency Knowledge Graph node with this identifier exists in the referenced graph snapshot.",
        ))
    else:
        reference, evidence_entry = _reference_and_evidence(
            record=node,
            record_id=node["node_id"],
            family=DEPENDENCY_KNOWLEDGE_GRAPH,
            source_locator_path=str(path),
            schema_version=DKG_SCHEMA_VERSION,
            derivation_path=DIRECT_DERIVATION_PATH,
            include_evidence=request.include_evidence,
            repo_commit=repo_commit,
        )
        references.append(reference)
        if evidence_entry:
            evidence.append(evidence_entry)
    limitations = list(graph.get("snapshot_limitations", []))
    return references, evidence, limitations, uncertainty


def _handle_historical_event_lookup(
    request: UnifiedQueryRequest, artifact_paths: dict[str, Path], repo_commit: str
) -> tuple[list, list, list, list]:
    path = artifact_paths[HISTORICAL_MEMORY]
    snapshot = artifact_loading.load_historical_memory(path)
    events = [e for e in snapshot.get("historical_events", []) if isinstance(e, dict)]
    event = find_by_id(events, FAMILY_ID_FIELDS[HISTORICAL_MEMORY], request.target or "")
    references: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    uncertainty: list[dict[str, Any]] = []
    if event is None:
        uncertainty.append(unresolved_identity_record(
            target=request.target or "",
            reason="No Historical Memory event with this identifier exists in the referenced snapshot.",
        ))
    else:
        reference, evidence_entry = _reference_and_evidence(
            record=event,
            record_id=event["event_id"],
            family=HISTORICAL_MEMORY,
            source_locator_path=str(path),
            schema_version=HISTORICAL_MEMORY_SCHEMA_VERSION,
            derivation_path=DIRECT_DERIVATION_PATH,
            include_evidence=request.include_evidence,
            repo_commit=repo_commit,
        )
        references.append(reference)
        if evidence_entry:
            evidence.append(evidence_entry)
    limitations = list(snapshot.get("snapshot_limitations", []))
    return references, evidence, limitations, uncertainty


def _handle_change_impact_entity_lookup(
    request: UnifiedQueryRequest, artifact_paths: dict[str, Path], repo_commit: str
) -> tuple[list, list, list, list]:
    path = artifact_paths[CHANGE_IMPACT]
    report = artifact_loading.load_change_impact(path)
    entities = [e for e in report.get("impacted_entities", []) if isinstance(e, dict)]
    entity = find_by_id(entities, FAMILY_ID_FIELDS[CHANGE_IMPACT], request.target or "")
    references: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    uncertainty: list[dict[str, Any]] = []
    if entity is None:
        uncertainty.append(unresolved_identity_record(
            target=request.target or "",
            reason="No Change Impact impacted entity with this identifier exists in the referenced report.",
        ))
    else:
        reference, evidence_entry = _reference_and_evidence(
            record=entity,
            record_id=entity["entity_id"],
            family=CHANGE_IMPACT,
            source_locator_path=str(path),
            schema_version=artifact_loading.NOT_APPLICABLE_PROTOTYPE_SHAPE,
            derivation_path=DIRECT_DERIVATION_PATH,
            include_evidence=request.include_evidence,
            repo_commit=repo_commit,
        )
        references.append(reference)
        if evidence_entry:
            evidence.append(evidence_entry)
    limitations = list(report.get("limitation_bundle", []))
    return references, evidence, limitations, uncertainty


def _handle_advisory_context_item_lookup(
    request: UnifiedQueryRequest, artifact_paths: dict[str, Path], repo_commit: str
) -> tuple[list, list, list, list]:
    path = artifact_paths[ADVISORY_CONTEXT]
    package = artifact_loading.load_advisory_context(path)
    items = [i for i in package.get("selected_repository_intelligence", []) if isinstance(i, dict)]
    item = find_by_id(items, FAMILY_ID_FIELDS[ADVISORY_CONTEXT], request.target or "")
    references: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    uncertainty: list[dict[str, Any]] = []
    if item is None:
        uncertainty.append(unresolved_identity_record(
            target=request.target or "",
            reason="No Advisory Context selected record with this identifier exists in the referenced package.",
        ))
    else:
        record_id = next(
            (item[f] for f in FAMILY_ID_FIELDS[ADVISORY_CONTEXT] if f in item),
            request.target or "",
        )
        reference, evidence_entry = _reference_and_evidence(
            record=item,
            record_id=record_id,
            family=ADVISORY_CONTEXT,
            source_locator_path=str(path),
            schema_version=artifact_loading.NOT_APPLICABLE_PROTOTYPE_SHAPE,
            derivation_path=DIRECT_DERIVATION_PATH,
            include_evidence=request.include_evidence,
            repo_commit=repo_commit,
        )
        references.append(reference)
        if evidence_entry:
            evidence.append(evidence_entry)
    limitations = list(package.get("limitation_bundle", []))
    return references, evidence, limitations, uncertainty


def _handle_cross_artifact_reference_lookup(
    request: UnifiedQueryRequest, artifact_paths: dict[str, Path], repo_commit: str
) -> tuple[list, list, list, list]:
    path = artifact_paths[CROSS_ARTIFACT_INTEGRATION]
    package = artifact_loading.load_cross_artifact_integration(path)
    resolutions = [r for r in package.get("entity_resolutions", []) if isinstance(r, dict)]
    resolution = find_by_id(resolutions, ("entity_id",), request.target or "")
    references: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    uncertainty: list[dict[str, Any]] = []
    if resolution is None:
        uncertainty.append(unresolved_identity_record(
            target=request.target or "",
            reason="No Cross-Artifact Integration entity resolution with this identifier exists in the referenced package.",
        ))
    else:
        reference, evidence_entry = _reference_and_evidence(
            record=resolution,
            record_id=resolution["entity_id"],
            family=CROSS_ARTIFACT_INTEGRATION,
            source_locator_path=str(path),
            schema_version=artifact_loading.NOT_APPLICABLE_PROTOTYPE_SHAPE,
            derivation_path=DIRECT_DERIVATION_PATH,
            include_evidence=request.include_evidence,
            repo_commit=repo_commit,
        )
        references.append(reference)
        if evidence_entry:
            evidence.append(evidence_entry)
    limitations = list(package.get("limitations", []))
    return references, evidence, limitations, uncertainty


def _handle_change_impact_to_dependency_node(
    request: UnifiedQueryRequest, artifact_paths: dict[str, Path], repo_commit: str
) -> tuple[list, list, list, list]:
    """The one explicitly-enumerated multi-family category (131B Section 12).

    Consumes Track 130's already-built Cross-Artifact Integration
    package directly -- never independently re-derives the
    Change-Impact-to-Dependency-Graph-node relationship.
    """
    integration_path = artifact_paths[CROSS_ARTIFACT_INTEGRATION]
    package = artifact_loading.load_cross_artifact_integration(integration_path)
    resolutions = [r for r in package.get("entity_resolutions", []) if isinstance(r, dict)]
    resolution = find_by_id(resolutions, ("entity_id",), request.target or "")

    references: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    uncertainty: list[dict[str, Any]] = []

    if resolution is None:
        unresolved = [u for u in package.get("unresolved_identities", []) if isinstance(u, dict)]
        miss = find_by_id(unresolved, ("entity_id",), request.target or "")
        reason = (
            miss.get("unresolved_reason")
            if miss
            else "No Cross-Artifact Integration entity resolution with this identifier exists in the referenced package."
        )
        uncertainty.append(unresolved_identity_record(target=request.target or "", reason=reason))
        return references, evidence, list(package.get("limitations", [])), uncertainty

    node_id = resolution["resolved_node_id"]
    node_record = {"entity_id": resolution["entity_id"], "resolved_node_id": node_id}
    reference, evidence_entry = _reference_and_evidence(
        record=node_record,
        record_id=node_id,
        family=DEPENDENCY_KNOWLEDGE_GRAPH,
        source_locator_path=str(integration_path),
        schema_version=DKG_SCHEMA_VERSION,
        derivation_path=(
            "via Track 130 Cross-Artifact Integration entity_resolutions: "
            f"change_impact entity {resolution['entity_id']!r} -> "
            f"dependency_context_reference {resolution.get('dependency_context_reference', 'unknown')!r} "
            f"-> dependency_knowledge_graph node {node_id!r}"
        ),
        include_evidence=request.include_evidence,
        repo_commit=repo_commit,
    )
    references.append(reference)
    if evidence_entry:
        evidence.append(evidence_entry)
    limitations = list(package.get("limitations", []))
    return references, evidence, limitations, uncertainty


_CATEGORY_HANDLERS = {
    "rks_entity_lookup": _handle_rks_entity_lookup,
    "dependency_node_lookup": _handle_dependency_node_lookup,
    "historical_event_lookup": _handle_historical_event_lookup,
    "change_impact_entity_lookup": _handle_change_impact_entity_lookup,
    "advisory_context_item_lookup": _handle_advisory_context_item_lookup,
    "cross_artifact_reference_lookup": _handle_cross_artifact_reference_lookup,
    "change_impact_to_dependency_node": _handle_change_impact_to_dependency_node,
}
