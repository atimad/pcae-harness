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
from .limits import DEFAULT_MAX_ISSUE_COUNT, DEFAULT_MAX_RECORD_DEPTH
from .models import OutcomeStatus, ShapeValidationResult, ValidationIssue
from .registry import SchemaRegistry


def _json_pointer(parts) -> str:
    if not parts:
        return ""
    escaped = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "/" + "/".join(escaped)


class _RejectedInput(Exception):
    """Internal signal: ``record`` cannot be safely materialized/validated."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


_PLAIN_SCALAR_TYPES = (str, int, float, bool)


def _materialize_plain(root: object, *, max_depth: int) -> object:
    """Iteratively (never recursively) rebuild ``root`` as an inert tree of
    plain ``dict``/``list``/``str``/``int``/``float``/``bool``/``None``,
    while also performing the Phase 136G nesting-depth check as a single
    pass.

    Phase 136H repair (``PREREQUISITE-136G-1``): ``validate_record_shape``'s
    docstring already required an already-strictly-parsed ``record`` (i.e.
    plain ``dict``/``list`` output of :func:`parse_strict_json`), but
    nothing enforced that at runtime -- a hostile ``Mapping`` subclass's
    ``__getitem__``/``.items()``/``__contains__`` could execute arbitrary
    code once handed directly to ``jsonschema``'s own traversal. This
    function accepts only exact ``dict``/``list`` containers (rejecting
    every other ``Mapping``/``Sequence`` implementation, and rejecting
    ``tuple`` as an unsupported container type, since ``parse_strict_json``
    never produces one), requires every ``dict`` key to be an exact ``str``,
    rejects any value whose exact type is not one of ``dict``/``list``/
    ``str``/``int``/``float``/``bool``/``None``, and rejects a cycle (a
    container that contains itself, directly or indirectly) using an
    explicit per-path ancestor-id set -- never a global memo, since the same
    sub-object legitimately appearing twice in unrelated branches is not a
    cycle. It never mutates ``root``; every returned container is newly
    built.

    Walked with an explicit stack, not recursion (Phase 136G's own
    established pattern): a genuinely deep or wide adversarial input must
    fail closed quickly, never raise an uncaught ``RecursionError`` while
    merely being measured.
    """
    if root is None or type(root) in _PLAIN_SCALAR_TYPES:
        return root
    if type(root) not in (dict, list):
        raise _RejectedInput(f"Unsupported top-level record type: {type(root).__name__}")

    def _new_frame(value: object, depth: int) -> dict:
        if depth > max_depth:
            raise _RejectedInput(f"Record nesting exceeds maximum depth of {max_depth}; refusing to validate")
        value_type = type(value)
        if value_type is dict:
            entries = []
            for key, child in value.items():
                if type(key) is not str:
                    raise _RejectedInput(f"Record contains a non-string mapping key: {key!r}")
                entries.append((key, child))
            return {"kind": "dict", "entries": entries, "pos": 0, "out": {}, "id": id(value), "depth": depth}
        if value_type is list:
            return {"kind": "list", "entries": list(value), "pos": 0, "out": [], "id": id(value), "depth": depth}
        raise _RejectedInput(f"Record contains an unsupported container type: {value_type.__name__}")

    path_ids: set[int] = set()
    root_frame = _new_frame(root, 0)
    path_ids.add(root_frame["id"])
    stack: list[dict] = [root_frame]

    while True:
        top = stack[-1]
        if top["pos"] >= len(top["entries"]):
            path_ids.discard(top["id"])
            stack.pop()
            finished = top["out"]
            if not stack:
                return finished
            parent = stack[-1]
            if parent["kind"] == "dict":
                parent_key = parent["entries"][parent["pos"] - 1][0]
                parent["out"][parent_key] = finished
            else:
                parent["out"].append(finished)
            continue

        if top["kind"] == "dict":
            _, value = top["entries"][top["pos"]]
        else:
            value = top["entries"][top["pos"]]
        top["pos"] += 1

        if value is None or type(value) in _PLAIN_SCALAR_TYPES:
            if top["kind"] == "dict":
                key = top["entries"][top["pos"] - 1][0]
                top["out"][key] = value
            else:
                top["out"].append(value)
            continue

        value_type = type(value)
        if value_type in (dict, list):
            if id(value) in path_ids:
                raise _RejectedInput("Record contains a cyclic (self-referential) structure")
            child_frame = _new_frame(value, top["depth"] + 1)
            path_ids.add(child_frame["id"])
            stack.append(child_frame)
            continue

        raise _RejectedInput(f"Record contains an unsupported value type: {value_type.__name__}")


def validate_record_shape(
    record: Mapping[str, object],
    *,
    schema_id: str,
    registry: SchemaRegistry,
    max_issues: int = DEFAULT_MAX_ISSUE_COUNT,
    max_record_depth: int = DEFAULT_MAX_RECORD_DEPTH,
) -> ShapeValidationResult:
    """Validate ``record`` against the schema registered as ``schema_id``.

    ``record`` must already have been produced by strict parsing.
    Unknown ``schema_id`` and unresolved ``$ref`` both fail closed as
    :attr:`OutcomeStatus.INFRASTRUCTURE_FAILURE`, distinct from an
    :attr:`OutcomeStatus.INVALID` record. A record nested deeper than
    ``max_record_depth`` also fails closed as
    :attr:`OutcomeStatus.INFRASTRUCTURE_FAILURE` (code
    ``internal_validation_error``) *before* the underlying validator is
    invoked, rather than risking an uncaught ``RecursionError`` from a
    self-referential schema traversing deep data (Phase 136G repair).

    ``record`` is also rejected, with the same
    :attr:`OutcomeStatus.INFRASTRUCTURE_FAILURE` status and
    ``internal_validation_error`` code, if it is not already an inert,
    plain-``dict``/``list``-rooted JSON-compatible structure: a hostile
    ``Mapping`` subclass, a non-``str`` mapping key, a cyclic (self-
    referential) container, or any container/scalar type other than
    ``dict``/``list``/``str``/``int``/``float``/``bool``/``None`` is
    rejected *before* the underlying validator ever sees it, rather than
    risking an untrusted object's dunder methods executing during
    ``jsonschema``'s own traversal (Phase 136H repair,
    ``PREREQUISITE-136G-1``). A plain, already-strictly-parsed ``dict``/
    ``list`` input is unaffected: it is rebuilt as an equal, freshly
    constructed plain structure and validated exactly as before; ``record``
    itself is never mutated.
    """
    try:
        plain_record = _materialize_plain(record, max_depth=max_record_depth)
    except _RejectedInput as exc:
        return ShapeValidationResult(
            status=OutcomeStatus.INFRASTRUCTURE_FAILURE,
            schema_id=schema_id,
            issues=(ValidationIssue(code="internal_validation_error", message=exc.message, schema_id=schema_id),),
        )

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
            validator.iter_errors(plain_record),
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

    # Phase 136G repair: status must reflect whether the record actually
    # failed validation (``errors``), not whether the *returned, possibly
    # truncated* ``issues`` tuple happens to be non-empty. Deciding status
    # from the truncated tuple meant max_issues=0 (or any cap smaller than
    # the true error count in an unlucky ordering) could silently report
    # OutcomeStatus.VALID for a genuinely invalid record -- a fail-open
    # misclassification of exactly the kind this package must never permit.
    if errors:
        return ShapeValidationResult(status=OutcomeStatus.INVALID, schema_id=schema_id, issues=issues)
    return ShapeValidationResult(status=OutcomeStatus.VALID, schema_id=schema_id, issues=())
