"""Repository Intelligence Service fail-closed exception model (132D Section 9).

Two new exception classes are introduced here; every other fail-closed
condition reuses an already-existing exception class from Unified
Query (``SnapshotLoadError``, ``SnapshotCompatibilityError``) rather
than multiplying the hierarchy -- the same discipline
``unified_query.errors`` itself already applies one layer down (131D
Section 8).
"""

from __future__ import annotations


class ServiceError(Exception):
    """Base class for errors raised by this package's own new exception types."""


class UnsupportedServiceRequestError(ServiceError):
    """Raised when a request names a kind/scope this contract does not define.

    132B Section 15: an unsupported request fails closed -- it is
    never guessed, defaulted, or silently partially honored.
    """


class MalformedServiceRequestError(ServiceError):
    """Raised for a structurally invalid request (132D Section 9's reused ValueError-translation pattern)."""
