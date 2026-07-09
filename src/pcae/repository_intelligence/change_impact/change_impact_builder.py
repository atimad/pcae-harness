from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pcae.repository_intelligence.change_impact.change_impact_report import (
    ChangeImpactReport,
)
from pcae.repository_intelligence.change_impact.change_request import (
    ChangeImpactRequest,
)
from pcae.repository_intelligence.change_impact.validation import (
    ChangeImpactValidationError,
    ensure_attribution_present,
    ensure_boundary_disclosure_present,
    ensure_limitation_present,
    validate_change_request,
    validate_query_result,
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
)

CHANGE_IMPACT_NON_AUTHORITY_DISCLAIMER = (
    "This Change Impact Report is descriptive Repository Intelligence "
    "reporting only. It is not Repository State, Evidence, Advisory output, "
    "Decision Evaluation, a recommendation, or execution authorization."
)

PROTOTYPE_SCOPE_LIMITATION = {
    "limitation_type": "change_impact_prototype_scope",
    "limitation_description": (
        "The prototype identifies directly returned Track 121 Query Layer "
        "entity records only. Dependency graph traversal, Historical Memory "
        "correlation, Advisory reasoning, recommendations, Decision "
        "Evaluation, execution planning, and execution capability are deferred."
    ),
}


class ChangeImpactBuilderError(Exception):
    """Raised when Change Impact report generation must fail closed."""


def build_change_impact_report(
    snapshot_path: Path, request: ChangeImpactRequest
) -> ChangeImpactReport:
    """Build a deterministic, read-only Change Impact Report.

    Repository Intelligence is consumed exclusively through the Track 121
    Query Layer. This function does not read Repository Intelligence artifacts
    directly, scan repositories, invoke generators, execute code, call
    subprocesses, or integrate with Advisory or Decision Evaluation.
    """
    try:
        validate_change_request(request)
    except ChangeImpactValidationError as exc:
        raise ChangeImpactBuilderError(str(exc)) from exc

    query_results: list[QueryResult] = []
    for target in sorted(request.target_entities):
        query_request = QueryRequest(category="entity_lookup", target=target)
        try:
            result = execute_query(snapshot_path, query_request)
            validate_query_result(result)
        except (
            QueryExecutionError,
            SnapshotCompatibilityError,
            SnapshotLoadError,
            ChangeImpactValidationError,
        ) as exc:
            raise ChangeImpactBuilderError(str(exc)) from exc
        query_results.append(result)

    impacted_entities = _identify_impacted_entities(query_results)
    impact_relationships = _identify_impact_relationships(query_results)
    attribution = _merge_unique_dicts(
        item for result in query_results for item in result.attribution
    )
    inherited_limitations = _merge_unique_dicts(
        item for result in query_results for item in result.limitations
    )
    limitations = _merge_unique_dicts(
        [PROTOTYPE_SCOPE_LIMITATION] + inherited_limitations
    )
    boundary_disclosures = _merge_boundaries(query_results, "boundary_disclosures")
    disclaimers = _merge_boundaries(query_results, "disclaimers")
    unknowns = tuple(
        sorted(
            {
                unknown
                for result in query_results
                for unknown in result.unknowns
            }
            | {
                f"no Query Layer entity record returned for target {result.query_metadata.get('target')!r}"
                for result in query_results
                if not result.records
            }
        )
    )

    try:
        ensure_limitation_present(inherited_limitations)
        ensure_attribution_present(impacted_entities, impact_relationships, attribution)
        ensure_boundary_disclosure_present(boundary_disclosures, disclaimers)
    except ChangeImpactValidationError as exc:
        raise ChangeImpactBuilderError(str(exc)) from exc

    boundary_disclosure_bundle: dict[str, Any] = {
        "boundary_disclosures": boundary_disclosures,
        "disclaimers": disclaimers,
        "non_authority_disclaimer": CHANGE_IMPACT_NON_AUTHORITY_DISCLAIMER,
    }
    source_artifacts = _merge_unique_dicts(
        result.source_artifact for result in query_results
    )
    query_requests = [
        {
            "category": result.query_metadata.get("category"),
            "target": result.query_metadata.get("target"),
        }
        for result in query_results
    ]

    metadata: dict[str, Any] = {
        "change_request": request.normalized(),
        "query_requests": query_requests,
        "source_artifacts": source_artifacts,
        "result_statuses": [result.result_status for result in query_results],
        "reporting_scope": "direct_query_layer_entity_records_only",
        "record_count": len(impacted_entities),
        "relationship_count": len(impact_relationships),
        "assembly_timestamp": datetime.now(timezone.utc).isoformat(),
        "unknowns": list(unknowns),
        "unavailable": [],
        "incomplete": [],
        "conflicting": [],
        "read_only_guarantee": {
            "direct_repository_intelligence_access": False,
            "repository_scanning": False,
            "repository_intelligence_generation": False,
            "subprocess_execution": False,
            "external_api_access": False,
            "runtime_mutation": False,
            "advisory_reasoning": False,
            "decision_evaluation": False,
        },
    }

    return ChangeImpactReport(
        impacted_entities=tuple(impacted_entities),
        impact_relationships=tuple(impact_relationships),
        attribution_bundle=tuple(attribution),
        limitation_bundle=tuple(limitations),
        boundary_disclosure_bundle=boundary_disclosure_bundle,
        report_metadata=metadata,
        unknowns=unknowns,
        unavailable=(),
        incomplete=(),
        conflicting=(),
    )


def _identify_impacted_entities(results: list[QueryResult]) -> list[dict[str, Any]]:
    impacted: list[dict[str, Any]] = []
    for result in results:
        target = result.query_metadata.get("target")
        for record in result.records:
            impacted.append(
                {
                    "entity_id": record.get("entity_id"),
                    "entity_name": record.get("entity_name"),
                    "entity_path": record.get("entity_path"),
                    "source_query": {
                        "category": result.query_metadata.get("category"),
                        "target": target,
                    },
                    "inclusion_criterion": "exact_query_layer_entity_match",
                    "repository_intelligence_record": record,
                }
            )
    return sorted(impacted, key=lambda item: (item.get("entity_id") or "", item.get("entity_path") or ""))


def _identify_impact_relationships(results: list[QueryResult]) -> list[dict[str, Any]]:
    relationships: list[dict[str, Any]] = []
    for result in results:
        target = result.query_metadata.get("target")
        for record in result.records:
            relationships.append(
                {
                    "relationship_type": "declared_change_target",
                    "change_target": target,
                    "impacted_entity": record.get("entity_id"),
                    "source_query": {
                        "category": result.query_metadata.get("category"),
                        "target": target,
                    },
                    "attribution": list(result.attribution),
                }
            )
    return sorted(
        relationships,
        key=lambda item: (item.get("change_target") or "", item.get("impacted_entity") or ""),
    )


def _merge_unique_dicts(items) -> list[dict[str, Any]]:
    unique: dict[str, dict[str, Any]] = {}
    for item in items:
        key = repr(_stable(item))
        unique[key] = item
    return [unique[key] for key in sorted(unique)]


def _merge_boundaries(results: list[QueryResult], field_name: str) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for result in results:
        value = getattr(result, field_name)
        for key in sorted(value):
            merged[key] = value[key]
    return merged


def _stable(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _stable(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_stable(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_stable(item) for item in value)
    return value
