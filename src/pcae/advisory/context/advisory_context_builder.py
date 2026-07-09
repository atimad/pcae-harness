from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pcae.advisory.context.context_package import (
    NON_AUTHORITY_DISCLAIMER,
    RepositoryIntelligenceContextPackage,
)
from pcae.advisory.context.context_request import AdvisoryContextRequest
from pcae.advisory.context.context_validation import (
    AdvisoryContextValidationError,
    ensure_attribution_present,
    ensure_boundary_disclosure_present,
    validate_context_request,
    validate_query_result,
)
from pcae.repository_intelligence.query.query_engine import (
    QueryExecutionError,
    execute_query,
)
from pcae.repository_intelligence.query.snapshot_loader import (
    SnapshotCompatibilityError,
    SnapshotLoadError,
)


class AdvisoryContextBuilderError(Exception):
    """Raised when Advisory context assembly must fail closed (122D
    S12). Wraps every underlying Track 121 Query Layer failure and
    every Advisory-context-layer validation failure behind one
    consumption-boundary exception, without repairing, guessing, or
    working around the underlying cause."""


def build_advisory_context(
    snapshot_path: Path, request: AdvisoryContextRequest
) -> RepositoryIntelligenceContextPackage:
    """Assemble a deterministic Repository Intelligence Advisory
    context package for ``request``.

    Consumes Repository Intelligence exclusively through the existing
    Track 121 ``execute_query`` entry point (122B S7, 122D S8). Never
    reads a Repository Knowledge Snapshot artifact directly, never
    reruns the Track 120 generator, and never scans the repository.
    Performs no reasoning, ranking beyond declared query scope, or
    decision making (122A S4, 122D S1).
    """
    try:
        validate_context_request(request)
    except AdvisoryContextValidationError as exc:
        raise AdvisoryContextBuilderError(str(exc)) from exc

    query_request = request.to_query_request()

    try:
        result = execute_query(snapshot_path, query_request)
    except (QueryExecutionError, SnapshotCompatibilityError, SnapshotLoadError) as exc:
        raise AdvisoryContextBuilderError(str(exc)) from exc

    try:
        validate_query_result(result)
    except AdvisoryContextValidationError as exc:
        raise AdvisoryContextBuilderError(str(exc)) from exc

    all_records = list(result.records)
    limitations = list(result.limitations)

    selected_records = all_records
    if request.max_records is not None and len(all_records) > request.max_records:
        selected_records = all_records[: request.max_records]
        limitations = limitations + [
            {
                "limitation_type": "context_bound",
                "limitation_description": (
                    f"Advisory context was bounded to {request.max_records} of "
                    f"{len(all_records)} matching records."
                ),
            }
        ]

    attribution = list(result.attribution)

    try:
        ensure_attribution_present(request.category, selected_records, attribution)
    except AdvisoryContextValidationError as exc:
        raise AdvisoryContextBuilderError(str(exc)) from exc

    try:
        ensure_boundary_disclosure_present(
            result.boundary_disclosures, result.disclaimers
        )
    except AdvisoryContextValidationError as exc:
        raise AdvisoryContextBuilderError(str(exc)) from exc

    boundary_disclosure_bundle: dict[str, Any] = {
        "boundary_disclosures": result.boundary_disclosures,
        "disclaimers": result.disclaimers,
        "non_authority_disclaimer": NON_AUTHORITY_DISCLAIMER,
    }

    context_metadata: dict[str, Any] = {
        "advisory_purpose": request.advisory_purpose,
        "query_request": {
            "category": query_request.category,
            "target": query_request.target,
        },
        "source_artifact": result.source_artifact,
        "result_status": result.result_status,
        "unknowns": list(result.unknowns),
        "record_count": len(selected_records),
        "assembly_timestamp": datetime.now(timezone.utc).isoformat(),
    }

    return RepositoryIntelligenceContextPackage(
        selected_repository_intelligence=tuple(selected_records),
        attribution_bundle=tuple(attribution),
        limitation_bundle=tuple(limitations),
        boundary_disclosure_bundle=boundary_disclosure_bundle,
        context_metadata=context_metadata,
    )
