"""Immutable generic result and error models for schema_runtime.

Phase 136F prerequisite infrastructure. These models carry no authority
role, no persistence side effect, and no implicit truth claim: a
``VALID`` :class:`ShapeValidationResult` means only that a record's
shape matched a schema, not that it is authoritative, published, or
semantically correct.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class OutcomeStatus(str, Enum):
    """Three-way outcome distinguishing valid input, invalid input, and
    infrastructure failure (e.g. an unknown schema id or unresolved
    reference), per the Phase 136F requirement that these remain
    distinguishable."""

    VALID = "valid"
    INVALID = "invalid"
    INFRASTRUCTURE_FAILURE = "infrastructure_failure"


@dataclass(frozen=True)
class ValidationIssue:
    """A single structured, machine-readable validation issue."""

    code: str
    message: str
    instance_path: str = ""
    schema_path: str = ""
    record_id: str | None = None
    schema_id: str | None = None


@dataclass(frozen=True)
class JsonParseResult:
    """Result of strict Layer-1 JSON parsing."""

    status: OutcomeStatus
    value: object
    errors: tuple[ValidationIssue, ...] = ()

    @property
    def ok(self) -> bool:
        return self.status is OutcomeStatus.VALID


@dataclass(frozen=True)
class ShapeValidationResult:
    """Result of generic Layer-2 shape validation against a schema.

    Carries no semantic or authority claim: it reports only whether a
    record's shape matches the referenced schema.
    """

    status: OutcomeStatus
    schema_id: str
    issues: tuple[ValidationIssue, ...] = ()

    @property
    def ok(self) -> bool:
        return self.status is OutcomeStatus.VALID


@dataclass(frozen=True)
class SchemaResourceInfo:
    """Read-only metadata describing a loaded schema resource."""

    schema_id: str
    relative_path: str
    dialect: str
    sha256: str
    size_bytes: int
