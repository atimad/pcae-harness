"""Publication Coordinator error hierarchy (Phase 144C; PEC-001 §11, §17).

Every error below fails closed: none repairs input, invents a default,
retries silently, or leaves partial effect (PEC-REQ-015, PEC-REQ-075).
Raising any of these SHALL correspond to "no publication occurred" --
never a partial write, per PEC-REQ-052/053/081.
"""
from __future__ import annotations


class PublicationExecutionError(Exception):
    """Base class for every Publication Coordinator error. A Publication
    Coordinator method that raises any subclass of this has performed no
    partial effect: no CHGR was created, and no prior evidence was
    mutated (PEC-REQ-052)."""


class MissingAuthorizationError(PublicationExecutionError):
    """No Publication Authorization Event was supplied at all
    (PEC-REQ-050, PEC-REQ-076). Distinct from ``InvalidAuthorizationError``,
    which covers a supplied-but-malformed or inapplicable event."""


class InvalidAuthorizationError(PublicationExecutionError):
    """A supplied Publication Authorization Event is malformed, or does
    not name the exact ``PublicationReadinessPackage`` under evaluation
    (PEC-REQ-040, PEC-REQ-088). Never repaired or reinterpreted -- refused
    outright."""


class AuthorizationReplayError(PublicationExecutionError):
    """The named ``package_id``/``session_id`` has already been consumed
    by a completed Publication Execution (PEC-REQ-007, PEC-REQ-041,
    PEC-REQ-042, PEC-REQ-078, PEC-REQ-080). Raised at the Coordinator's
    single entry point, before any write is attempted, or -- if lost to a
    genuine concurrent race at the atomic commit step -- after the
    just-written record has been rolled back (PEC-REQ-053)."""


class StaleAuthorizationError(PublicationExecutionError):
    """A Publication Authorization Event names a package that has since
    become invalid, or whose authorization timestamp cannot have followed
    the package's own construction (PEC-REQ-079). The Coordinator
    re-verifies at execution time; it never trusts a prior check."""


class InvalidPublicationPackageError(PublicationExecutionError):
    """The supplied package fails ``is_ready()``, is not a
    ``PublicationReadinessPackage`` instance, or is found to carry a
    prohibited field (PEC-REQ-049, PEC-REQ-064, PEC-REQ-077)."""


class AtomicPublicationFailure(PublicationExecutionError):
    """The atomic write stage failed for a reason not covered by a more
    specific subclass below. No CHGR was left in canonical storage
    (PEC-REQ-081)."""


class PublicationStorageError(AtomicPublicationFailure):
    """The CHGR write could not be durably persisted (PEC-REQ-082). The
    Coordinator never reports success while storage has not durably
    completed the write."""


class PublicationRollbackError(AtomicPublicationFailure):
    """A failure occurred after the atomic write began but before
    Publication Execution could be reported complete, and the
    Coordinator's deterministic rollback of the just-written record itself
    failed or required explicit reporting (PEC-REQ-053, PEC-REQ-081)."""


class ChgrSchemaConformanceError(PublicationExecutionError):
    """The constructed four-artifact CHGR set (``human_governance_record``,
    ``human_confirmation_evidence``, ``governance_record_provenance``,
    ``governance_record_integrity``) does not validate against the frozen
    CHGR-001 v1.2 schema family, or CHGR-REQ-208's non-schema disclosure
    check failed (CHGR-REQ-204, CHGR-REQ-205; Phase 146G). Raised strictly
    before any artifact is written: no CHGR of any kind is created, and no
    Publication attempt partially succeeds."""


__all__ = [
    "AtomicPublicationFailure",
    "AuthorizationReplayError",
    "ChgrSchemaConformanceError",
    "InvalidAuthorizationError",
    "InvalidPublicationPackageError",
    "MissingAuthorizationError",
    "PublicationExecutionError",
    "PublicationRollbackError",
    "PublicationStorageError",
    "StaleAuthorizationError",
]
