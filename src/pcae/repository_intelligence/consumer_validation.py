from __future__ import annotations

from collections.abc import Sequence
from typing import Any, TypeVar

ValidationErrorT = TypeVar("ValidationErrorT", bound=Exception)


def validate_query_result_shape(
    result: Any,
    *,
    required_fields: Sequence[str],
    error_type: type[ValidationErrorT],
) -> None:
    """Validate the shared Query Layer result shape at consumer boundaries."""
    for field in required_fields:
        if not hasattr(result, field):
            raise error_type(f"invalid Query Layer result: missing field {field!r}")
    if not isinstance(result.source_artifact, dict) or not result.source_artifact.get(
        "executable_schema_version"
    ):
        raise error_type(
            "invalid Query Layer result: source_artifact is missing executable_schema_version"
        )


def ensure_records_have_attribution(
    *,
    has_content: bool,
    attribution: Sequence[dict[str, Any]],
    error_type: type[ValidationErrorT],
    message: str,
) -> None:
    """Fail closed when content-bearing consumer output lacks attribution."""
    if has_content and not attribution:
        raise error_type(message)


def ensure_limitations_present(
    limitations: Sequence[dict[str, Any]],
    *,
    error_type: type[ValidationErrorT],
) -> None:
    """Fail closed when inherited Repository Intelligence limitations are absent."""
    if not limitations:
        raise error_type("Query Layer result is missing required limitation records")


def ensure_boundary_material_present(
    boundary_disclosures: dict[str, Any],
    disclaimers: dict[str, Any],
    *,
    error_type: type[ValidationErrorT],
) -> None:
    """Fail closed when both boundary disclosures and disclaimers are absent."""
    if not boundary_disclosures and not disclaimers:
        raise error_type(
            "Query Layer result is missing both boundary_disclosures and disclaimers"
        )
