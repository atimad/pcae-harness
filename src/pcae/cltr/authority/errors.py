"""Typed-model error hierarchy for the Stage 3 typed-authority shared core
(136Y plan Sec.29).

Distinct from ``src/pcae/schema_runtime/errors.py`` (Layer 1/2 concerns:
strict-parse, schema-validation), which is reused unchanged and never
duplicated here. Every error below is a Layer 3 (typed-model construction/
serialization) concern only.

Errors never repair input, downgrade a failure to a warning, invent a
default value, mutate repository state, disclose secret-like field
contents, or claim authority truth in their message text (136Y plan
Sec.29-30).
"""

from __future__ import annotations


class TypedModelError(Exception):
    """Base class for every Layer 3 typed-model error."""


class TypedModelConstructionError(TypedModelError):
    """A schema-valid payload nonetheless fails a typed-model-layer check
    (enum re-validation, digest-shape re-validation, reference-shape
    re-validation, absent/null misuse outside a contract-named
    relaxation)."""


class InvalidIdentifierError(TypedModelConstructionError):
    """An identifier value does not match its owning wrapper type's frozen
    local-syntax rule."""


class InvalidDigestError(TypedModelConstructionError):
    """A digest value is not a well-formed 64-character lowercase hex
    SHA-256 string. Never raised to "correct" a mismatch -- shape only."""


class InvalidReferenceError(TypedModelConstructionError):
    """A reference tuple's shape is invalid, or its family tag does not
    match the caller's required family."""


class WrongFamilyReferenceError(InvalidReferenceError):
    """A family-restricted reference field was constructed with a
    ``record_family`` tag other than the field's required constant."""


class InvalidTimestampError(TypedModelConstructionError):
    """A timestamp string does not match the frozen wire pattern."""


class UnsupportedJsonValueError(TypedModelConstructionError):
    """A Python value supplied to an opaque-JSON or immutable-container
    constructor is not one of the JSON-compatible types this package
    accepts (no arbitrary objects, functions, bytes, sets)."""


class AbsentNullMismatchError(TypedModelConstructionError):
    """A payload supplies ``null`` for a field where the schema forbids
    null but permits absence (or vice versa), outside a contract-named
    exception (e.g. ``CutoverRequest`` Sec.6.3)."""


class UnsupportedSchemaVersionError(TypedModelError):
    """``from_dict``/``from_json`` was called with a ``schema_version`` the
    model class does not explicitly recognize. No fallback to "latest
    assumed" is ever performed."""


class UnknownModelFamilyError(TypedModelError):
    """A dispatcher was asked to construct a model for a family with no
    registered model class."""


class OpaqueValuePreservationError(TypedModelError):
    """Internal invariant failure: an opaque field's round-trip produced a
    value unequal to its input. Defensive only -- should be unreachable in
    a correct implementation."""


class SerializationError(TypedModelError):
    """``to_dict``/``to_canonical_bytes`` encountered an internal state
    inconsistency (e.g. an unsupported Python value reached the
    serializer, or a required field somehow holds ``ABSENT``)."""


class TypedModelInternalInvariantError(TypedModelError):
    """A structural invariant check failed on a payload that passed schema
    validation -- indicates either a genuinely malformed input the schema
    under-constrains, or a plan/schema drift bug."""


class RoundTripMismatchError(TypedModelError):
    """Test-only: raised by test-suite round-trip assertion helpers so a
    round-trip failure produces a specific, named failure rather than a
    bare ``AssertionError``. Never raised by production code."""


__all__ = [
    "TypedModelError",
    "TypedModelConstructionError",
    "InvalidIdentifierError",
    "InvalidDigestError",
    "InvalidReferenceError",
    "WrongFamilyReferenceError",
    "InvalidTimestampError",
    "UnsupportedJsonValueError",
    "AbsentNullMismatchError",
    "UnsupportedSchemaVersionError",
    "UnknownModelFamilyError",
    "OpaqueValuePreservationError",
    "SerializationError",
    "TypedModelInternalInvariantError",
    "RoundTripMismatchError",
]
