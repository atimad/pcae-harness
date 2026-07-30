"""``pcae.authority_evaluation`` -- standalone Authority Evaluation Model.

Implements AEMIC-001 v1.2's public domain model, pure evaluator, Registry
abstraction (ABC only), and serialization helpers. This package is a
disclosed evaluation, never an authorization: no name, type, or function
below grants, blocks, or conditions Confirmation, Readiness, Authorization,
or Publication.

Public re-exports only (AEMIC-REQ-014); no logic lives here.
"""

from __future__ import annotations

from pcae.authority_evaluation.errors import (
    AuthorityEvaluationError,
    AuthorityRegistryCorruptError,
    AuthorityRegistryUnavailableError,
    InvalidClaimedIdentityError,
    InvalidTemplateReferenceError,
    MalformedDeclarationError,
    MissingCitationTextError,
    TemplateIdentityMismatchError,
    UnsupportedSchemaVersionError,
)
from pcae.authority_evaluation.evaluation import evaluate
from pcae.authority_evaluation.models import (
    AuthorityEvaluationOutcome,
    EligibleAuthorityDeclaration,
    EvaluationResult,
)
from pcae.authority_evaluation.registry import AuthorityRegistry

__all__ = [
    "EligibleAuthorityDeclaration",
    "AuthorityEvaluationOutcome",
    "EvaluationResult",
    "evaluate",
    "AuthorityRegistry",
    "AuthorityEvaluationError",
    "InvalidClaimedIdentityError",
    "InvalidTemplateReferenceError",
    "MalformedDeclarationError",
    "UnsupportedSchemaVersionError",
    "MissingCitationTextError",
    "TemplateIdentityMismatchError",
    "AuthorityRegistryUnavailableError",
    "AuthorityRegistryCorruptError",
]
