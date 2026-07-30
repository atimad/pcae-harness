"""The pure ``evaluate`` function (AEMIC-001 v1.2 §14).

``evaluate`` has no Registry dependency: it never calls
``AuthorityRegistry.resolve``, never imports
``pcae.authority_evaluation.registry``, and performs no I/O of any kind
(AEMIC-REQ-073). The Registry lookup is always performed by ``evaluate``'s
own caller, upstream, exactly once, with the result passed in as the
``declaration`` parameter.

Disclosure-only (§8): this function resolves a registered Declaration,
validates the structural shape of its own inputs, and discloses why a
Declaration could not establish eligibility or did not exist at all. It
never determines legal authority, never grants/denies/authorizes
anything, and never elevates runtime, execution, or Permission Broker
capability in any way.
"""

from __future__ import annotations

from typing import Optional

from pcae.authority_evaluation.errors import (
    InvalidClaimedIdentityError,
    InvalidTemplateReferenceError,
    MissingCitationTextError,
    TemplateIdentityMismatchError,
)
from pcae.authority_evaluation.models import (
    AuthorityEvaluationOutcome,
    EligibleAuthorityDeclaration,
    EvaluationResult,
)

_DECLARATION_REF_SEPARATOR = "::"


def _declaration_ref(template_ref: str, template_version: str) -> str:
    """Deterministically derive ``declaration_ref`` from the identity
    tuple (§10.2, AEMIC-REQ-038) -- never an opaque, storage-specific
    identifier."""

    return f"{template_ref}{_DECLARATION_REF_SEPARATOR}{template_version}"


def evaluate(
    template_ref: str,
    template_version: str,
    claimed_identity: str,
    declaration: Optional[EligibleAuthorityDeclaration],
    evaluated_at: str,
    evaluator_version: str,
    citation_text: Optional[str] = None,
) -> AuthorityEvaluationOutcome:
    """Disclose whether ``claimed_identity`` is a member of the eligible
    set declared for ``(template_ref, template_version)``.

    This function is total, non-raising for every well-formed input
    (AEMIC-REQ-074), deterministic (AEMIC-REQ-075/105), and side-effect
    free (AEMIC-REQ-076). It is a disclosed evaluation, never an
    authorization: a matching template identity does not, by itself,
    prove authority (AEMIC-REQ-107).

    Error precedence (AEMIC-REQ-104), evaluated strictly in this order,
    a more authoritative earlier check never masked by a later one
    (AEMIC-REQ-105):

    1. ``template_ref``/``template_version`` structural validity.
    2. ``claimed_identity`` structural validity.
    3. If ``declaration`` is non-``None``, its own identity must agree
       with (1)'s already-validated parameters.
    4. ``evaluation_result`` is determined from exactly the two
       evidentiary inputs (``claimed_identity``, ``declaration``).
    5. If ``evaluation_result`` is ``ELIGIBLE`` and ``citation_text`` is
       ``None``, raise.
    """

    if not isinstance(template_ref, str) or template_ref == "":
        raise InvalidTemplateReferenceError(
            f"template_ref must be a non-empty str, got {template_ref!r}."
        )
    if not isinstance(template_version, str) or template_version == "":
        raise InvalidTemplateReferenceError(
            f"template_version must be a non-empty str, got {template_version!r}."
        )

    if not isinstance(claimed_identity, str) or claimed_identity == "":
        raise InvalidClaimedIdentityError(
            f"claimed_identity must be a non-empty str, got {claimed_identity!r}."
        )

    if declaration is not None:
        if (
            declaration.template_ref != template_ref
            or declaration.template_version != template_version
        ):
            raise TemplateIdentityMismatchError(
                "declaration's own (template_ref, template_version) "
                f"({declaration.template_ref!r}, {declaration.template_version!r}) "
                f"disagrees with evaluate's own ({template_ref!r}, {template_version!r})."
            )

    if declaration is not None and claimed_identity in declaration.eligible_identities:
        evaluation_result = EvaluationResult.ELIGIBLE
    elif declaration is not None:
        evaluation_result = EvaluationResult.INELIGIBLE
    else:
        evaluation_result = EvaluationResult.INDETERMINATE

    if evaluation_result is EvaluationResult.ELIGIBLE and citation_text is None:
        raise MissingCitationTextError(
            "evaluation_result is ELIGIBLE but citation_text is None; a "
            "well-formed ELIGIBLE outcome always carries a citation."
        )

    if evaluation_result is EvaluationResult.ELIGIBLE:
        outcome_citation_text = citation_text
    else:
        # Disregarded, not fabricated into the outcome and not treated as
        # caller error (AEMIC-REQ-065/101 step 4).
        outcome_citation_text = None

    outcome_declaration_ref = (
        _declaration_ref(template_ref, template_version) if declaration is not None else None
    )

    return AuthorityEvaluationOutcome(
        template_ref=template_ref,
        template_version=template_version,
        claimed_identity=claimed_identity,
        evaluation_result=evaluation_result,
        declaration_ref=outcome_declaration_ref,
        citation_text=outcome_citation_text,
        evaluated_at=evaluated_at,
        evaluator_version=evaluator_version,
    )


__all__ = ["evaluate"]
