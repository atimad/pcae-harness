"""Integration-level error taxonomy for the Authority Evaluation Service
(AESIC-001 v1.3 §5.7, §13, AESIC-REQ-010).

Distinct from ``pcae.authority_evaluation.errors`` (AEMIC-001's own
taxonomy, raised by the frozen ``models``/``evaluation`` modules and by a
concrete ``AuthorityRegistry`` implementation's ``resolve()``): every
exception below is owned by the integration surface this package's
``service``/``resolution``/``storage`` modules implement, never by the
pure evaluator or its model types.

AES translates every collaborator failure into one of these named
outcomes (AESIC-REQ-016); it never raises a bare ``Exception`` and never
raises a type not named in this taxonomy (AESIC-REQ-010).
"""

from __future__ import annotations

from enum import Enum


class AuthorityEvaluationIntegrationError(Exception):
    """Base exception for every failure this integration surface defines."""


# --- AES's own translated Registry conditions (AESIC-REQ-016) --------------


class AuthorityEvaluationServiceRegistryUnavailableError(AuthorityEvaluationIntegrationError):
    """AES's own translation of a Registry ``AuthorityRegistryUnavailableError``."""


class AuthorityEvaluationServiceRegistryCorruptError(AuthorityEvaluationIntegrationError):
    """AES's own translation of a Registry ``AuthorityRegistryCorruptError``."""


# --- Decision Template Resolution failures (§6.4, AESIC-REQ-033) -----------


class DecisionTemplateNotFoundError(AuthorityEvaluationIntegrationError):
    """No template document exists for ``(template_ref, template_version)``."""


class DecisionTemplateMalformedError(AuthorityEvaluationIntegrationError):
    """A template document exists but fails schema validation."""


class DecisionTemplateCitationEmptyError(AuthorityEvaluationIntegrationError):
    """A template document validates but ``eligible_authority`` is empty/whitespace."""


class DecisionTemplateResolutionFailedError(AuthorityEvaluationIntegrationError):
    """AES's own surfaced condition for a missing/malformed Decision Template
    (AESIC-REQ-016), wrapping one of the three Resolution failures above."""


# --- Stage 1 handoff validation (§5.2.1, AESIC-REQ-123/124) ----------------


class Stage1HandoffInvalidReason(Enum):
    MALFORMED = "malformed"
    SESSION_MISMATCH = "session_mismatch"
    IDENTITY_MISMATCH = "identity_mismatch"
    TEMPLATE_MISMATCH = "template_mismatch"


class Stage1HandoffInvalidError(AuthorityEvaluationIntegrationError):
    """A caller-supplied ``stage_1_result`` failed one of AESIC-REQ-123's
    four validation checks (AESIC-REQ-124). Carries a closed, four-member
    ``reason`` -- never a bare ``str``."""

    def __init__(self, reason: Stage1HandoffInvalidReason, message: str) -> None:
        if not isinstance(reason, Stage1HandoffInvalidReason):
            raise TypeError(
                f"Stage1HandoffInvalidError.reason must be a Stage1HandoffInvalidReason, "
                f"got {reason!r}."
            )
        super().__init__(message)
        self.reason = reason


# --- Canonical pointer failures (§12.1, AESIC-REQ-126/127/130/131) ---------


class CanonicalPointerCorruptError(AuthorityEvaluationIntegrationError):
    """A canonical pointer's own ``pointer_digest`` or referenced-AER digest
    failed read-time verification (AESIC-REQ-126/127) -- fail-closed; the
    mismatched pointer's referenced content SHALL NOT be treated as
    canonical."""


class CanonicalPointerUpdateFailedError(AuthorityEvaluationIntegrationError):
    """A pointer write failed synchronously within the same
    ``evaluate_stage_2`` call, immediately after a successful AER commit
    (AESIC-REQ-130 item 7, AESIC-REQ-131). The already-committed AER is
    never mutated or deleted; the caller retries."""


# --- AER persistence failures (§12, storage layer) --------------------------


class AuthorityEvaluationRecordConflictError(AuthorityEvaluationIntegrationError):
    """An exclusive-create write for ``(package_id, evaluation_id)`` collided
    with an already-existing entry (AESIC-REQ-019) -- reachable only if
    ``evaluation_id`` uniqueness (AESIC-REQ-098) were somehow violated;
    treated as a defense-in-depth corruption guard, never the mechanism
    deciding idempotent reuse vs. supersession (that is AESIC-REQ-023's own,
    made before any write is attempted)."""


class AuthorityEvaluationRecordCorruptError(AuthorityEvaluationIntegrationError):
    """A persisted AER failed read-time digest verification (AESIC-REQ-055)."""


class AuthorityEvaluationStorageIdentifierError(AuthorityEvaluationIntegrationError):
    """A ``package_id``/``evaluation_id`` supplied to
    ``AuthorityEvaluationRecordStore`` is not usable, verbatim, as a single
    AER/pointer storage path component (Phase 147P persistence-boundary
    hardening, 147O.2-F-1). Raised before any filesystem access is
    attempted; the identifier is rejected, never rewritten or normalized."""


class AuthorityEvaluationSerializationError(AuthorityEvaluationIntegrationError):
    """AES's own AER (or pointer) serialization/canonicalization failed
    (§13's ``Serialization failure`` row) -- an AES bug to fix, never
    retryable without a code change."""


__all__ = [
    "AuthorityEvaluationIntegrationError",
    "AuthorityEvaluationServiceRegistryUnavailableError",
    "AuthorityEvaluationServiceRegistryCorruptError",
    "DecisionTemplateNotFoundError",
    "DecisionTemplateMalformedError",
    "DecisionTemplateCitationEmptyError",
    "DecisionTemplateResolutionFailedError",
    "Stage1HandoffInvalidReason",
    "Stage1HandoffInvalidError",
    "CanonicalPointerCorruptError",
    "CanonicalPointerUpdateFailedError",
    "AuthorityEvaluationRecordConflictError",
    "AuthorityEvaluationRecordCorruptError",
    "AuthorityEvaluationStorageIdentifierError",
    "AuthorityEvaluationSerializationError",
]
