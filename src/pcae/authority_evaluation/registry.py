"""``AuthorityRegistry`` abstract interface only (AEMIC-001 v1.2 §11).

A concrete, storage-backed implementation is explicitly deferred from
this package's first implementation scope (AEMIC-REQ-008): this module
contains the ABC and nothing else -- no filesystem backend, no
persistence, no caching, no discovery logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from pcae.authority_evaluation.models import EligibleAuthorityDeclaration


class AuthorityRegistry(ABC):
    """Read-only lookup of eligible-authority Declarations.

    Exposes exactly one abstract method (AEMIC-REQ-042): no ``create``,
    ``persist``, ``delete``, ``list``, or ``enumerate`` method exists on
    this ABC -- every consumer this contract defines has read-only access,
    full stop.
    """

    @abstractmethod
    def resolve(
        self, template_ref: str, template_version: str
    ) -> Optional[EligibleAuthorityDeclaration]:
        """Return the Declaration for ``(template_ref, template_version)``.

        SHALL be a pure function of its two inputs at any fixed point in
        time (AEMIC-REQ-043). SHALL return ``None``, never raise, for a
        pair with no matching Declaration (AEMIC-REQ-044) -- "no
        Declaration exists" is an ordinary, expected outcome, not an
        error condition.

        A concrete implementation MUST raise
        ``AuthorityRegistryUnavailableError`` if its own storage layer
        could not be consulted at all, and
        ``AuthorityRegistryCorruptError`` if the storage layer answered
        but the record is structurally malformed or a duplicate/conflict
        was detected (§11.2-§11.3, AEMIC-REQ-045-049) -- neither
        exception is raised by this ABC itself, since no concrete
        implementation exists in this module.
        """
        raise NotImplementedError


__all__ = ["AuthorityRegistry"]
