"""Repository Intelligence Service lifecycle orchestration (132B Section 6): nine stages, no additional ones.

1. Service request        -- ``ServiceRequest`` (caller-supplied).
2. Request validation      -- ``request.normalize_service_request``.
3. Unified Query invocation -- ``unified_query.execute_unified_query``,
   called exclusively; no duplicated routing, identity resolution, or
   artifact loading anywhere in this module.
4. Response composition    -- this module's ``_compose`` function.
5. Provenance assembly     -- carried forward unchanged from each
   consumed ``UnifiedQueryResponse``.
6. Evidence assembly       -- carried forward unchanged, opt-in.
7. Limitation propagation  -- union of every consumed call's own
   limitations plus Service-level composition limitations.
8. Boundary disclosure propagation -- the same real nine-field object
   Unified Query's own ``boundary.py`` already reuses, propagated
   unchanged.
9. Service response        -- deterministic serialization in
   ``ServiceResponse``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pcae.repository_intelligence.service.errors import (
    MalformedServiceRequestError,
    UnsupportedServiceRequestError,
)
from pcae.repository_intelligence.service.request import (
    ServiceRequest,
    normalize_service_request,
    resolve_scope,
)
from pcae.repository_intelligence.service.response import ServiceResponse
from pcae.repository_intelligence.unified_query import (
    UnifiedQueryRequest,
    execute_unified_query,
)
from pcae.repository_intelligence.unified_query.boundary import (
    unified_query_boundary_disclosures,
    unified_query_boundary_notes,
)
from pcae.repository_intelligence.query.snapshot_loader import (
    SnapshotCompatibilityError,
    SnapshotLoadError,
)
from pcae.repository_intelligence.unified_query.routing import (
    ADVISORY_CONTEXT,
    CHANGE_IMPACT,
    CROSS_ARTIFACT_INTEGRATION,
    DEPENDENCY_KNOWLEDGE_GRAPH,
    HISTORICAL_MEMORY,
    REPOSITORY_KNOWLEDGE_SNAPSHOT,
)

# Reuses Unified Query's own six single-family categories exclusively
# -- no new routing table, no new category is introduced by this
# package (132B Section 3: Unified Query is the sole access path).
FAMILY_TO_CATEGORY: dict[str, str] = {
    REPOSITORY_KNOWLEDGE_SNAPSHOT: "rks_entity_lookup",
    DEPENDENCY_KNOWLEDGE_GRAPH: "dependency_node_lookup",
    HISTORICAL_MEMORY: "historical_event_lookup",
    CHANGE_IMPACT: "change_impact_entity_lookup",
    ADVISORY_CONTEXT: "advisory_context_item_lookup",
    CROSS_ARTIFACT_INTEGRATION: "cross_artifact_reference_lookup",
}


def execute_service_request(
    request: ServiceRequest,
    *,
    artifact_paths: dict[str, Path],
    repo_commit: str = "unknown",
) -> ServiceResponse:
    """Execute the full nine-stage Repository Intelligence Service lifecycle.

    ``artifact_paths`` maps artifact family name to the path of that
    family's already-generated artifact on disk -- the same mapping
    shape Unified Query's own ``execute_unified_query`` already
    accepts; this function never reads an artifact file itself, it
    only ever forwards paths to Unified Query.

    Never mutates any artifact, the repository, or runtime state.
    Every failure path raises an already-planned exception (132D
    Section 9) or produces an explicit uncertainty/limitation record
    -- never a silent omission, never an inferred recovery.
    """
    # Stage 1-2: request + validation.
    try:
        metadata = normalize_service_request(request)
    except ValueError as exc:
        raise MalformedServiceRequestError(str(exc)) from exc

    if request.kind == "composite":
        return _execute_composite(request, metadata, artifact_paths=artifact_paths, repo_commit=repo_commit)
    return _execute_single(request, metadata, artifact_paths=artifact_paths, repo_commit=repo_commit)


def _execute_single(
    request: ServiceRequest,
    metadata: dict[str, Any],
    *,
    artifact_paths: dict[str, Path],
    repo_commit: str,
) -> ServiceResponse:
    families = resolve_scope(request)
    if not families:
        raise UnsupportedServiceRequestError(
            f"service request kind {request.kind!r} resolved to an empty family scope"
        )

    per_family: dict[str, dict[str, Any]] = {}
    composition_metadata: list[dict[str, Any]] = []
    limitations: list[dict[str, Any]] = []
    uncertainty: list[dict[str, Any]] = []
    any_reference = False

    # Stage 3-8, one Unified Query call per resolved family, in fixed
    # declared order (never re-ordered by content or outcome).
    for family in families:
        category = FAMILY_TO_CATEGORY[family]
        if family not in artifact_paths:
            composition_metadata.append(
                {"family": family, "category": category, "status": "skipped", "reason": "no artifact path supplied"}
            )
            limitations.append(
                {
                    "limitation_type": "scope_limitation",
                    "limitation_description": f"{family} was not queried: no artifact path was supplied for it.",
                }
            )
            continue

        uq_request = UnifiedQueryRequest(
            category=category, target=request.target, include_evidence=request.include_evidence
        )
        try:
            result = execute_unified_query(
                uq_request, artifact_paths={family: artifact_paths[family]}, repo_commit=repo_commit
            )
        except (SnapshotLoadError, SnapshotCompatibilityError) as exc:
            composition_metadata.append(
                {"family": family, "category": category, "status": "failed", "reason": str(exc)}
            )
            limitations.append(
                {
                    "limitation_type": "scope_limitation",
                    "limitation_description": f"{family} could not be queried: {exc}",
                }
            )
            continue

        composition_metadata.append(
            {"family": family, "category": category, "status": "queried", "result_status": result.result_status}
        )
        per_family[family] = {
            "references": list(result.references),
            "evidence": list(result.evidence),
            "limitations": list(result.limitations),
            "uncertainty": list(result.uncertainty),
        }
        limitations.extend(result.limitations)
        uncertainty.extend(result.uncertainty)
        if result.references:
            any_reference = True

    # No silent omission: if nothing was ever actually queried (every
    # family skipped or failed), and no limitation/uncertainty record
    # exists to explain why, force one explicit record rather than
    # returning an empty "ok" response -- directly preserving the
    # Track 131/132 silent-omission invariant (132B Section 15) at
    # this composition layer, not merely inheriting it by accident.
    if not any_reference and not uncertainty and not limitations:
        uncertainty.append(
            {
                "entity_id": request.target or "",
                "uncertainty_state": "unresolved",
                "unresolved_reason": "No family in the resolved scope could be queried or matched the requested identifier.",
            }
        )

    result_status = "ok" if any_reference else "unknown"

    # Stage 9: response delivery -- deterministic serialization.
    return ServiceResponse(
        request_metadata=metadata,
        families=per_family,
        composition_metadata=tuple(composition_metadata),
        limitations=tuple(_sort_by_description(limitations)),
        uncertainty=tuple(sorted(uncertainty, key=lambda u: u.get("entity_id", ""))),
        boundary_disclosures=unified_query_boundary_disclosures(),
        boundary_notes=tuple(unified_query_boundary_notes()),
        result_status=result_status,
    )


def _execute_composite(
    request: ServiceRequest,
    metadata: dict[str, Any],
    *,
    artifact_paths: dict[str, Path],
    repo_commit: str,
) -> ServiceResponse:
    """The one explicitly-enumerated composite shape (132D Section 5).

    Executes N independent inner requests, each fully composed via
    ``_execute_single``, then wraps them in one outer envelope --
    never correlating across targets. Cross-target reasoning remains
    explicitly deferred (132D Section 5's own bounding of this scope).
    """
    inner_responses: list[ServiceResponse] = []
    for inner in request.composite_targets:
        inner_metadata = normalize_service_request(inner)
        inner_responses.append(
            _execute_single(inner, inner_metadata, artifact_paths=artifact_paths, repo_commit=repo_commit)
        )

    # Deterministic ordering: by inner target, identifier-lexicographic
    # (matching every other Repository Intelligence array's own
    # ordering discipline).
    inner_responses.sort(key=lambda response: response.request_metadata.get("target") or "")

    overall_status = "ok" if any(response.result_status == "ok" for response in inner_responses) else "unknown"

    return ServiceResponse(
        request_metadata=metadata,
        families={},
        composition_metadata=(),
        limitations=(),
        uncertainty=(),
        boundary_disclosures=unified_query_boundary_disclosures(),
        boundary_notes=tuple(unified_query_boundary_notes()),
        result_status=overall_status,
        composite_responses=tuple(inner_responses),
    )


def _sort_by_description(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for record in sorted(records, key=lambda r: r.get("limitation_description", "")):
        key = record.get("limitation_description", "")
        if key in seen:
            continue
        seen.add(key)
        unique.append(record)
    return unique
