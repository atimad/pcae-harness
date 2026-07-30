"""Exception hierarchy for ``pcae.authority_evaluation`` (AEMIC-001 v1.2 §13).

Two architecturally distinct families, restating AEMIC-REQ-067:

- §13.1 (structural / malformed-input failures): raised by ``models.py``
  and ``evaluation.py`` against caller-supplied, well-formed-or-not
  inputs. Never raised by a Registry's own ``resolve``.
- §13.2 (Registry / infrastructure failures): raised exclusively by a
  concrete ``AuthorityRegistry`` implementation's own ``resolve`` method
  (none exists in this package, AEMIC-REQ-008). Never raised by
  ``evaluate`` itself, which never touches storage (AEMIC-REQ-073/077).

No condition is collapsed into a generic ``ValueError``, ``RuntimeError``,
or bare ``Exception`` where a named type above already exists
(AEMIC-REQ-070). ``AuthorityEvaluationError`` itself is raised directly
only for an internal invariant violation this taxonomy did not otherwise
anticipate (AEMIC-REQ-069).
"""

from __future__ import annotations


class AuthorityEvaluationError(Exception):
    """Base exception for every failure this package defines."""


# --- §13.1 Structural (malformed-input) failures ---------------------------


class InvalidClaimedIdentityError(AuthorityEvaluationError):
    """``claimed_identity`` is empty or not a ``str``."""


class InvalidTemplateReferenceError(AuthorityEvaluationError):
    """``template_ref`` or ``template_version`` is empty or not a ``str``."""


class MalformedDeclarationError(AuthorityEvaluationError):
    """A Declaration's own construction-time invariant is violated."""


class UnsupportedSchemaVersionError(AuthorityEvaluationError):
    """A payload's ``schema_version`` does not match a known value."""


class MissingCitationTextError(AuthorityEvaluationError):
    """``evaluation_result`` is ``ELIGIBLE`` but ``citation_text`` is ``None``."""


class TemplateIdentityMismatchError(AuthorityEvaluationError):
    """``declaration``'s own identity disagrees with ``evaluate``'s own
    ``template_ref``/``template_version`` parameters (repairs BF-147F.1-1).

    Distinct from, and never collapsed into (AEMIC-REQ-106):
    ``InvalidTemplateReferenceError`` (a structural/format defect, not a
    disagreement between two well-formed values); ``INDETERMINATE`` (a
    mismatch means a Declaration *did* resolve, just not for the identity
    also supplied); either §13.2 Registry exception (Registry-`resolve`-time
    only); or ``MissingCitationTextError`` (an unrelated, later-ordered
    check).
    """


# --- §13.2 Registry (infrastructure) failures -------------------------------


class AuthorityRegistryUnavailableError(AuthorityEvaluationError):
    """A concrete Registry's own storage layer could not be consulted at all."""


class AuthorityRegistryCorruptError(AuthorityEvaluationError):
    """A concrete Registry's own storage layer answered but is malformed,
    or a duplicate/conflicting record was detected (AEMIC-REQ-045/048)."""


__all__ = [
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
