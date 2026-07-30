"""Public domain model for ``pcae.authority_evaluation`` (AEMIC-001 v1.2 §4-§7).

Every type below is disclosure-only (§8): none is named, documented, or
shaped in a way a reasonable downstream consumer could mistake for an
authorization decision. This module contains no Registry lookup, no I/O,
and no evaluation logic of its own (those live in ``registry.py`` and
``evaluation.py`` respectively).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import FrozenSet, Optional

from pcae.authority_evaluation.errors import MalformedDeclarationError

DECLARATION_SCHEMA_VERSION = "aem-declaration/1.0"
OUTCOME_SCHEMA_VERSION = "aem-outcome/1.0"

#: This package's own published evaluator-version constant (§10.4,
#: AEMIC-REQ-040). Callers pass this unchanged; it is descriptive
#: metadata only, never itself evaluated.
EVALUATOR_VERSION = "aem-evaluator/1.0"


def _non_empty_str(value: object, field_name: str) -> str:
    if not isinstance(value, str) or value == "":
        raise MalformedDeclarationError(
            f"{field_name!s} must be a non-empty str, got {value!r}."
        )
    return value


def _parseable_iso8601(value: object, field_name: str) -> str:
    text = _non_empty_str(value, field_name)
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise MalformedDeclarationError(
            f"{field_name!s} must be a parseable ISO-8601 timestamp, got {value!r}."
        ) from exc
    return text


class EvaluationResult(Enum):
    """The closed, three-value evaluation outcome (§7, AEMIC-REQ-024-026).

    A plain ``Enum``, never a bare ``str`` (AEMIC-REQ-026): an invalid
    fourth value is a construction-time error, not a silently-accepted
    typo.
    """

    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True)
class EligibleAuthorityDeclaration:
    """An immutable record of a declared eligible-authority set for one
    Decision Template identity (§4, AEMIC-REQ-015-018).

    Carries exactly six fields; no other field is defined for v1.0
    (AEMIC-REQ-016). ``declared_by`` is recorded for provenance only and
    is never itself evaluated (AEM-REQ-013).
    """

    template_ref: str
    template_version: str
    eligible_identities: FrozenSet[str]
    declared_at: str
    declared_by: str
    schema_version: str = field(default=DECLARATION_SCHEMA_VERSION)

    def __post_init__(self) -> None:
        _non_empty_str(self.template_ref, "template_ref")
        _non_empty_str(self.template_version, "template_version")

        if not isinstance(self.eligible_identities, frozenset) or len(self.eligible_identities) == 0:
            raise MalformedDeclarationError(
                "eligible_identities must be a non-empty frozenset[str]."
            )
        for member in self.eligible_identities:
            _non_empty_str(member, "eligible_identities member")

        _parseable_iso8601(self.declared_at, "declared_at")
        _non_empty_str(self.declared_by, "declared_by")

        if self.schema_version != DECLARATION_SCHEMA_VERSION:
            raise MalformedDeclarationError(
                f"schema_version must equal exactly {DECLARATION_SCHEMA_VERSION!r}, "
                f"got {self.schema_version!r}."
            )


@dataclass(frozen=True)
class AuthorityEvaluationOutcome:
    """An immutable record of one evaluation's own disclosed result
    (§6, AEMIC-REQ-021-023).

    Carries exactly eight fields. ``citation_text is not None`` if and
    only if ``evaluation_result == EvaluationResult.ELIGIBLE`` (§6.1,
    AEMIC-REQ-022) -- enforced here, at construction time, not left to
    caller discipline. This is a disclosed evaluation result, never an
    authorization: a matching identity does not, by itself, prove
    authority (AEMIC-REQ-107).
    """

    template_ref: str
    template_version: str
    claimed_identity: str
    evaluation_result: EvaluationResult
    declaration_ref: Optional[str]
    citation_text: Optional[str]
    evaluated_at: str
    evaluator_version: str
    schema_version: str = field(default=OUTCOME_SCHEMA_VERSION)

    def __post_init__(self) -> None:
        _non_empty_str(self.template_ref, "template_ref")
        _non_empty_str(self.template_version, "template_version")
        _non_empty_str(self.claimed_identity, "claimed_identity")

        if not isinstance(self.evaluation_result, EvaluationResult):
            raise MalformedDeclarationError(
                f"evaluation_result must be an EvaluationResult, got {self.evaluation_result!r}."
            )

        is_eligible = self.evaluation_result is EvaluationResult.ELIGIBLE
        if is_eligible and self.citation_text is None:
            raise MalformedDeclarationError(
                "citation_text must be non-None when evaluation_result is ELIGIBLE."
            )
        if not is_eligible and self.citation_text is not None:
            raise MalformedDeclarationError(
                "citation_text must be None when evaluation_result is not ELIGIBLE."
            )

        if self.declaration_ref is not None and not isinstance(self.declaration_ref, str):
            raise MalformedDeclarationError("declaration_ref must be a str or None.")

        _parseable_iso8601(self.evaluated_at, "evaluated_at")
        _non_empty_str(self.evaluator_version, "evaluator_version")

        if self.schema_version != OUTCOME_SCHEMA_VERSION:
            raise MalformedDeclarationError(
                f"schema_version must equal exactly {OUTCOME_SCHEMA_VERSION!r}, "
                f"got {self.schema_version!r}."
            )


__all__ = [
    "DECLARATION_SCHEMA_VERSION",
    "OUTCOME_SCHEMA_VERSION",
    "EVALUATOR_VERSION",
    "EvaluationResult",
    "EligibleAuthorityDeclaration",
    "AuthorityEvaluationOutcome",
]
