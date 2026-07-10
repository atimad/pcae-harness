"""Unified Query fail-closed exception model (131D Section 8).

Two new exception classes are introduced here; every other fail-closed
condition reuses an already-existing exception class from Track 121
(``query.snapshot_loader``) rather than multiplying the hierarchy
(131D Section 8's own planning table).
"""

from __future__ import annotations


class UnifiedQueryError(Exception):
    """Base class for errors raised by this package's own new exception types."""


class UnsupportedQueryCategoryError(UnifiedQueryError):
    """Raised when a request names a category absent from the declared routing table.

    131B Section 7 / 131D Section 4: an unroutable category fails
    closed -- it is never guessed, defaulted, or routed to the
    "nearest" family.
    """


class RoutingAmbiguityError(UnifiedQueryError):
    """Raised when a category resolves to more than one family with no declared rule.

    131D Section 4: every multi-family category must be explicitly
    enumerated in the declared routing table before it may be
    implemented. A category that resolves to multiple families without
    appearing in the explicit multi-family allow-list fails closed
    rather than being handled by an improvised disambiguation rule.
    """
