"""Generic Layer-2 shape-validation API.

Phase 136F prerequisite infrastructure. Validates that an already
strictly-parsed record's *shape* matches an explicitly selected Draft
2020-12 schema. This API makes no semantic or authority claim: a
``VALID`` result means the record's shape matched the schema, nothing
more. It performs no mutation, network, subprocess, shell, or backend
invocation.
"""
from __future__ import annotations

from typing import Mapping

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError as _JsonSchemaError
from referencing.exceptions import Unresolvable as _Unresolvable

from .errors import SchemaRegistryError
from .limits import DEFAULT_MAX_ISSUE_COUNT
from .models import OutcomeStatus, ShapeValidationResult, ValidationIssue
from .registry import SchemaRegistry


def _json_pointer(parts) -> str:
    if not parts:
        return ""
    escaped = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "/" + "/".join(escaped)


def validate_record_shape(
    record: Mapping[str, object],
    *,
    schema_id: str,
    registry: SchemaRegistry,
    max_issues: int = DEFAULT_MAX_ISSUE_COUNT,
) -> ShapeValidationResult:
    """Validate ``record`` against the schema registered as ``schema_id``.

    ``record`` must already have been produced by strict parsing.
    Unknown ``schema_id`` and unresolved ``$ref`` both fail closed as
    :attr:`OutcomeStatus.INFRASTRUCTURE_FAILURE`, distinct from an
    :attr:`OutcomeStatus.INVALID` record.
    """
    try:
        schema = registry.document(schema_id)
    except SchemaRegistryError:
        return ShapeValidationResult(
            status=OutcomeStatus.INFRASTRUCTURE_FAILURE,
            schema_id=schema_id,
            issues=(ValidationIssue(code="unknown_schema", message=f"Unknown schema id: {schema_id}"),),
        )

    try:
        validator = Draft202012Validator(schema, registry=registry.referencing_registry)
    except _JsonSchemaError as exc:
        return ShapeValidationResult(
            status=OutcomeStatus.INFRASTRUCTURE_FAILURE,
            schema_id=schema_id,
            issues=(ValidationIssue(code="schema_resource_invalid", message=str(exc), schema_id=schema_id),),
        )

    try:
        errors = sorted(
            validator.iter_errors(record),
            key=lambda err: ([str(p) for p in err.absolute_path], str(err.validator)),
        )
    except (_Unresolvable, SchemaRegistryError) as exc:
        return ShapeValidationResult(
            status=OutcomeStatus.INFRASTRUCTURE_FAILURE,
            schema_id=schema_id,
            issues=(
                ValidationIssue(
                    code="schema_reference_unresolved",
                    message=str(exc),
                    schema_id=schema_id,
                ),
            ),
        )

    issues = tuple(
        ValidationIssue(
            code="schema_invalid_record",
            message=err.message,
            instance_path=_json_pointer(err.absolute_path),
            schema_path=_json_pointer(err.absolute_schema_path),
            schema_id=schema_id,
        )
        for err in errors[:max_issues]
    )

    if issues:
        return ShapeValidationResult(status=OutcomeStatus.INVALID, schema_id=schema_id, issues=issues)
    return ShapeValidationResult(status=OutcomeStatus.VALID, schema_id=schema_id, issues=())
