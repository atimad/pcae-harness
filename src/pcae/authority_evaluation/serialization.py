"""``to_payload``/``from_payload`` for both record types (AEMIC-001 v1.2 §18).

``to_payload`` returns a plain ``dict`` suitable for
``json.dumps(..., sort_keys=True)`` (AEMIC-REQ-088); whitespace/indentation
is a storage-layer concern this module does not decide (AEMIC-REQ-089).
No digest is computed over either record type (AEMIC-REQ-092, a
deliberate, disclosed non-requirement). Unicode is round-tripped
byte-for-byte with no normalization (AEMIC-REQ-090).
"""

from __future__ import annotations

from typing import Any, Dict

from pcae.authority_evaluation.errors import (
    MalformedDeclarationError,
    UnsupportedSchemaVersionError,
)
from pcae.authority_evaluation.models import (
    DECLARATION_SCHEMA_VERSION,
    OUTCOME_SCHEMA_VERSION,
    AuthorityEvaluationOutcome,
    EligibleAuthorityDeclaration,
    EvaluationResult,
)

_KNOWN_DECLARATION_SCHEMA_VERSIONS = frozenset({DECLARATION_SCHEMA_VERSION})
_KNOWN_OUTCOME_SCHEMA_VERSIONS = frozenset({OUTCOME_SCHEMA_VERSION})


def declaration_to_payload(declaration: EligibleAuthorityDeclaration) -> Dict[str, Any]:
    """Serialize ``declaration`` to a plain, JSON-compatible ``dict``."""

    return {
        "template_ref": declaration.template_ref,
        "template_version": declaration.template_version,
        "eligible_identities": sorted(declaration.eligible_identities),
        "declared_at": declaration.declared_at,
        "declared_by": declaration.declared_by,
        "schema_version": declaration.schema_version,
    }


def declaration_from_payload(payload: Dict[str, Any]) -> EligibleAuthorityDeclaration:
    """Deserialize a plain ``dict`` into an ``EligibleAuthorityDeclaration``.

    Raises ``UnsupportedSchemaVersionError`` for any ``schema_version``
    this package does not recognize (checked first, AEMIC-REQ-093), and
    ``MalformedDeclarationError`` for any other missing, ``null``, or
    structurally invalid field (AEMIC-REQ-091).
    """

    schema_version = payload.get("schema_version")
    if schema_version not in _KNOWN_DECLARATION_SCHEMA_VERSIONS:
        raise UnsupportedSchemaVersionError(
            f"Unsupported EligibleAuthorityDeclaration schema_version: {schema_version!r}."
        )

    try:
        eligible_identities = payload["eligible_identities"]
        if eligible_identities is None:
            raise MalformedDeclarationError("eligible_identities must not be null.")
        return EligibleAuthorityDeclaration(
            template_ref=payload["template_ref"],
            template_version=payload["template_version"],
            eligible_identities=frozenset(eligible_identities),
            declared_at=payload["declared_at"],
            declared_by=payload["declared_by"],
            schema_version=schema_version,
        )
    except KeyError as exc:
        raise MalformedDeclarationError(
            f"EligibleAuthorityDeclaration payload missing required field: {exc}."
        ) from exc
    except TypeError as exc:
        raise MalformedDeclarationError(
            f"EligibleAuthorityDeclaration payload malformed: {exc}."
        ) from exc


def outcome_to_payload(outcome: AuthorityEvaluationOutcome) -> Dict[str, Any]:
    """Serialize ``outcome`` to a plain, JSON-compatible ``dict``."""

    return {
        "template_ref": outcome.template_ref,
        "template_version": outcome.template_version,
        "claimed_identity": outcome.claimed_identity,
        "evaluation_result": outcome.evaluation_result.value,
        "declaration_ref": outcome.declaration_ref,
        "citation_text": outcome.citation_text,
        "evaluated_at": outcome.evaluated_at,
        "evaluator_version": outcome.evaluator_version,
        "schema_version": outcome.schema_version,
    }


def outcome_from_payload(payload: Dict[str, Any]) -> AuthorityEvaluationOutcome:
    """Deserialize a plain ``dict`` into an ``AuthorityEvaluationOutcome``.

    Raises ``UnsupportedSchemaVersionError`` for any ``schema_version``
    this package does not recognize (checked first, AEMIC-REQ-093), and
    ``MalformedDeclarationError`` for any other missing, ``null``, or
    structurally invalid field, including a ``citation_text``/
    ``evaluation_result`` combination violating the if-and-only-if
    invariant (§6.1, enforced by ``AuthorityEvaluationOutcome``'s own
    constructor).
    """

    schema_version = payload.get("schema_version")
    if schema_version not in _KNOWN_OUTCOME_SCHEMA_VERSIONS:
        raise UnsupportedSchemaVersionError(
            f"Unsupported AuthorityEvaluationOutcome schema_version: {schema_version!r}."
        )

    try:
        evaluation_result_value = payload["evaluation_result"]
        if evaluation_result_value is None:
            raise MalformedDeclarationError("evaluation_result must not be null.")
        try:
            evaluation_result = EvaluationResult(evaluation_result_value)
        except ValueError as exc:
            raise MalformedDeclarationError(
                f"Unrecognized evaluation_result: {evaluation_result_value!r}."
            ) from exc

        return AuthorityEvaluationOutcome(
            template_ref=payload["template_ref"],
            template_version=payload["template_version"],
            claimed_identity=payload["claimed_identity"],
            evaluation_result=evaluation_result,
            declaration_ref=payload["declaration_ref"],
            citation_text=payload["citation_text"],
            evaluated_at=payload["evaluated_at"],
            evaluator_version=payload["evaluator_version"],
            schema_version=schema_version,
        )
    except KeyError as exc:
        raise MalformedDeclarationError(
            f"AuthorityEvaluationOutcome payload missing required field: {exc}."
        ) from exc
    except TypeError as exc:
        raise MalformedDeclarationError(
            f"AuthorityEvaluationOutcome payload malformed: {exc}."
        ) from exc


__all__ = [
    "declaration_to_payload",
    "declaration_from_payload",
    "outcome_to_payload",
    "outcome_from_payload",
]
