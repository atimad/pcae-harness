from __future__ import annotations

from typing import Any

from pcae.advisory.context.context_request import (
    SUPPORTED_CONTEXT_CATEGORIES,
    AdvisoryContextRequest,
)

#: Categories whose records carry attribution (122B S9). Limitation and
#: boundary lookups return snapshot-level material, not attributable
#: content-bearing records, mirroring the Track 121 Query Layer's own
#: `_collect_attribution` exemption (query_engine.py).
CONTENT_BEARING_CATEGORIES = frozenset(
    {
        "entity_lookup",
        "capability_lookup",
        "architectural_contract_lookup",
        "attribution_lookup",
    }
)


class AdvisoryContextValidationError(Exception):
    """Raised when an Advisory context request or Query Layer result
    fails validation and must fail closed (122D S12)."""


def validate_context_request(request: AdvisoryContextRequest) -> None:
    """Fail closed for an invalid Advisory context request (122D S12,
    "invalid context request")."""
    if request.category not in SUPPORTED_CONTEXT_CATEGORIES:
        raise AdvisoryContextValidationError(
            f"unsupported advisory context category: {request.category}"
        )
    if not request.advisory_purpose or not request.advisory_purpose.strip():
        raise AdvisoryContextValidationError(
            "advisory context request requires a declared, non-empty advisory_purpose"
        )
    if request.category in {
        "entity_lookup",
        "capability_lookup",
        "architectural_contract_lookup",
        "attribution_lookup",
    } and not request.target:
        raise AdvisoryContextValidationError(
            f"{request.category} requires a target"
        )
    if request.max_records is not None and request.max_records < 1:
        raise AdvisoryContextValidationError(
            "max_records must be a positive integer when provided"
        )


def validate_query_result(result: Any) -> None:
    """Fail closed for an invalid Query Layer result (122D S12, "invalid
    query response"). The Query Layer already guarantees these fields;
    this is a defensive re-check at the consumption boundary, never a
    substitute for the Query Layer's own validation."""
    required_fields = (
        "query_metadata",
        "source_artifact",
        "records",
        "attribution",
        "limitations",
        "boundary_disclosures",
        "disclaimers",
        "result_status",
    )
    for field in required_fields:
        if not hasattr(result, field):
            raise AdvisoryContextValidationError(
                f"invalid Query Layer result: missing field {field!r}"
            )
    if not isinstance(result.source_artifact, dict) or not result.source_artifact.get(
        "executable_schema_version"
    ):
        raise AdvisoryContextValidationError(
            "invalid Query Layer result: source_artifact is missing executable_schema_version"
        )


def ensure_attribution_present(
    category: str,
    selected_records: list[dict[str, Any]],
    attribution: list[dict[str, Any]],
) -> None:
    """Fail closed if content-bearing selected records exist without
    attribution (122B S9, 122D S12 "missing attribution"). Missing
    attribution is a context assembly failure, never a silently
    unattributed inclusion."""
    if category not in CONTENT_BEARING_CATEGORIES:
        return
    if selected_records and not attribution:
        raise AdvisoryContextValidationError(
            "content-bearing selected records are missing required attribution"
        )


def ensure_boundary_disclosure_present(
    boundary_disclosures: dict[str, Any], disclaimers: dict[str, Any]
) -> None:
    """Fail closed if the source Query Result carries no boundary
    disclosure or disclaimer material at all (122D S12, "missing
    boundary disclosure"). An empty dict from a genuinely
    boundary-free snapshot is a Query Layer contract violation, not an
    Advisory-context-layer repair target -- it fails closed here rather
    than assembling a package with a silently missing boundary."""
    if not boundary_disclosures and not disclaimers:
        raise AdvisoryContextValidationError(
            "Query Layer result is missing both boundary_disclosures and disclaimers"
        )
