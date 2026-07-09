from __future__ import annotations

from typing import Any

from pcae.repository_intelligence.change_impact.change_request import (
    ChangeImpactRequest,
)
from pcae.repository_intelligence.consumer_validation import (
    ensure_boundary_material_present,
    ensure_limitations_present,
    ensure_records_have_attribution,
    validate_query_result_shape,
)


SUPPORTED_CHANGE_IMPACT_EVALUATION_SCOPE = frozenset({"entity_lookup"})


class ChangeImpactValidationError(Exception):
    """Raised when Change Impact reporting must fail closed."""


def validate_change_request(request: ChangeImpactRequest) -> None:
    if not request.requested_change or not request.requested_change.strip():
        raise ChangeImpactValidationError(
            "Change Impact request requires a non-empty requested_change"
        )
    if not request.target_entities:
        raise ChangeImpactValidationError(
            "Change Impact request requires at least one target entity"
        )
    if any(not target or not target.strip() for target in request.target_entities):
        raise ChangeImpactValidationError(
            "Change Impact request target entities must be non-empty"
        )
    unsupported = sorted(
        set(request.evaluation_scope) - SUPPORTED_CHANGE_IMPACT_EVALUATION_SCOPE
    )
    if unsupported:
        raise ChangeImpactValidationError(
            "unsupported Change Impact evaluation scope: " + ", ".join(unsupported)
        )


def validate_query_result(result: Any) -> None:
    required_fields = (
        "query_metadata",
        "source_artifact",
        "records",
        "attribution",
        "limitations",
        "unknowns",
        "boundary_disclosures",
        "disclaimers",
        "result_status",
    )
    validate_query_result_shape(
        result,
        required_fields=required_fields,
        error_type=ChangeImpactValidationError,
    )


def ensure_attribution_present(
    impacted_entities: list[dict[str, Any]],
    impact_relationships: list[dict[str, Any]],
    attribution: list[dict[str, Any]],
) -> None:
    ensure_records_have_attribution(
        has_content=bool(impacted_entities or impact_relationships),
        attribution=attribution,
        error_type=ChangeImpactValidationError,
        message="impacted entities or relationships are missing required attribution",
    )


def ensure_limitation_present(limitations: list[dict[str, Any]]) -> None:
    ensure_limitations_present(limitations, error_type=ChangeImpactValidationError)


def ensure_boundary_disclosure_present(
    boundary_disclosures: dict[str, Any], disclaimers: dict[str, Any]
) -> None:
    ensure_boundary_material_present(
        boundary_disclosures,
        disclaimers,
        error_type=ChangeImpactValidationError,
    )
