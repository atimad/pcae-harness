"""Immutable Evidence domain model (IWC-001 v1.1 §8, Phase 143M).

Evidence is informational only. This module deliberately carries no
authority field, no approval field, no confirmation field, and no CHGR
linkage -- Decision Session evidence is a snapshot presented for human
review, never itself a governance act or a claim of one (IWC-001 v1.1
§8.2, §14; Phase 143J §16 Evidence Coordinator row: "None -- never ranks
or weights").

Nothing here evaluates, scores, or ranks evidence; that is a permanently
prohibited capability for this package (IWC-REQ-081), not merely an
unbuilt one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Mapping, Optional


EVIDENCE_SCHEMA_VERSION = "interactive-workflow-evidence/0.1"


class EvidenceAvailability(str, Enum):
    """Whether a piece of evidence resolved cleanly, is an explicit gap,
    or is in conflict with another cited item (IWC-001 v1.1 §8.3,
    IWC-REQ-084, IWC-REQ-085). No "trusted"/"verified" member exists --
    uncertainty is surfaced, never resolved on the caller's behalf."""

    AVAILABLE = "Available"
    GAP = "Gap"
    CONFLICTED = "Conflicted"


def _frozen_metadata(value: Optional[Mapping[str, object]]) -> Mapping[str, object]:
    if value is None:
        return MappingProxyType({})
    return MappingProxyType(dict(value))


@dataclass(frozen=True)
class EvidenceItem:
    """A single, immutable evidence record.

    Fields mirror IWC-001 v1.1 §8's evidence discipline: an identifier, a
    template-declared type, a provenance reference carried alongside the
    citation (IWC-REQ-082, never asserted separately), a collection
    timestamp, an availability state (§8.3), and a metadata container for
    template-declared attributes this package does not itself interpret.
    """

    evidence_id: str
    evidence_type: str
    provenance_ref: str
    collected_at: str
    availability: EvidenceAvailability
    metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not self.evidence_id:
            raise ValueError("EvidenceItem.evidence_id must be non-empty.")
        if not self.evidence_type:
            raise ValueError("EvidenceItem.evidence_type must be non-empty.")
        if not self.provenance_ref:
            raise ValueError("EvidenceItem.provenance_ref must be non-empty.")
        if not self.collected_at:
            raise ValueError("EvidenceItem.collected_at must be non-empty.")
        if not isinstance(self.availability, EvidenceAvailability):
            raise ValueError(
                f"EvidenceItem.availability must be an EvidenceAvailability member, "
                f"got {self.availability!r}."
            )
        object.__setattr__(self, "metadata", _frozen_metadata(self.metadata))


__all__ = [
    "EVIDENCE_SCHEMA_VERSION",
    "EvidenceAvailability",
    "EvidenceItem",
]
