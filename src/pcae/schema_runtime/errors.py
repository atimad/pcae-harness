"""Narrow Layer-1/Layer-2 error vocabulary for schema_runtime.

Phase 136F prerequisite infrastructure only. These codes describe shape
and parsing failures. They are deliberately distinct from future
semantic/authority error categories (identity mismatch, digest mismatch,
stale authorization, CAS rejection, authority conflict, recovery
required), none of which are implemented by this package.
"""
from __future__ import annotations

# Layer-1 (strict JSON parsing) and Layer-2 (schema/shape validation)
# machine-readable error codes.
ERROR_CODES = frozenset(
    {
        "invalid_utf8",
        "input_too_large",
        "invalid_json",
        "duplicate_key",
        "non_finite_number",
        "top_level_not_object",
        "unknown_schema",
        "unsupported_schema_version",
        "unsupported_dialect",
        "schema_resource_invalid",
        "schema_reference_unresolved",
        "schema_invalid_record",
        "internal_validation_error",
    }
)


class SchemaRuntimeError(Exception):
    """Base class for programmer-error exceptions raised by schema_runtime.

    Normal invalid input (malformed JSON, duplicate keys, non-finite
    numbers, invalid records) is reported through result objects, not
    exceptions. These exceptions are reserved for misuse of the API
    itself (e.g. an untrusted or missing schema resource root).
    """


class SchemaResourceError(SchemaRuntimeError):
    """Raised when a schema resource cannot be trusted or loaded safely."""


class SchemaResourceNotFoundError(SchemaResourceError):
    """Raised when a requested schema resource does not exist.

    Kept distinct from :class:`SchemaResourceError` so callers can tell
    a missing resource apart from an invalid one.
    """


class SchemaRegistryError(SchemaRuntimeError):
    """Raised for misuse of the offline schema registry."""
