"""Evidence Coordinator (IWC-001 v1.1 §8, Phase 143J §16, Phase 143M).

The sole production owner of evidence registration, evidence ordering,
evidence validation, and evidence availability reporting for a single
Decision Session (Phase 143J §16 Evidence Coordinator row). No other
production component may register, order, or report on evidence.

Integration with the Session Infrastructure (143K) and Transition Engine
(143L) is structural and passive only: a coordinator is scoped to one
session identifier, validated with the same ``CDS-<uuid4>`` syntax check
the Session Coordinator itself uses (``pcae.interactive_workflow.session.
identity.validate_session_id``), but this module never calls
``SessionCoordinator`` or ``TransitionEngine`` -- it cannot drive a
transition, and it does not try to.

This coordinator does not, and per its governing phase prompt never will,
evaluate evidence, score evidence, recommend an action, decide session
readiness, or transition a session. Those methods do not exist on this
class; there is nothing to disable.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

from pcae.interactive_workflow.errors import DuplicateEvidenceError, UnknownEvidenceError
from pcae.interactive_workflow.evidence.models import EvidenceItem
from pcae.interactive_workflow.session.identity import validate_session_id


class EvidenceCoordinator:
    """Registers and orders evidence for exactly one Decision Session."""

    def __init__(self, session_id: str) -> None:
        self._session_id = validate_session_id(session_id)
        self._items: Dict[str, EvidenceItem] = {}

    @property
    def session_id(self) -> str:
        return self._session_id

    def register(self, item: EvidenceItem) -> EvidenceItem:
        """Register a new evidence item.

        Raises ``DuplicateEvidenceError`` if ``item.evidence_id`` is
        already registered -- the existing entry is never silently
        overwritten (fail closed).
        """

        if item.evidence_id in self._items:
            raise DuplicateEvidenceError(
                f"Evidence identifier {item.evidence_id!r} is already registered "
                f"for session {self._session_id!r}."
            )
        self._items[item.evidence_id] = item
        return item

    def get(self, evidence_id: str) -> EvidenceItem:
        """Return the registered evidence item for ``evidence_id``.

        Raises ``UnknownEvidenceError`` if no such item is registered.
        """

        try:
            return self._items[evidence_id]
        except KeyError as exc:
            raise UnknownEvidenceError(
                f"No evidence registered for identifier {evidence_id!r}."
            ) from exc

    def ordered_view(self) -> Tuple[EvidenceItem, ...]:
        """Return every registered evidence item in deterministic order.

        Ordering is a pure function of content -- ``(collected_at,
        evidence_id)`` -- never registration order, so two coordinators
        fed the same evidence set in different registration orders
        produce an identical view (IWC-REQ-079's determinism requirement,
        restated at the ordering layer).
        """

        return tuple(
            sorted(self._items.values(), key=lambda i: (i.collected_at, i.evidence_id))
        )

    def report_missing(self, declared_evidence_ids: Iterable[str]) -> Tuple[str, ...]:
        """Return, in the given order, every declared evidence identifier
        that is not currently registered (IWC-REQ-084: an unresolvable
        declared class SHALL be presented as an explicit gap, never
        omitted silently)."""

        missing: List[str] = [
            evidence_id
            for evidence_id in declared_evidence_ids
            if evidence_id not in self._items
        ]
        return tuple(missing)


__all__ = ["EvidenceCoordinator"]
