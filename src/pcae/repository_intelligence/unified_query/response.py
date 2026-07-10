"""Unified Query response model: a closed six-category shape (131B Section 8 / 131D Section 11.2).

No field may exist outside references/provenance/evidence/limitations/
uncertainty/boundary-disclosures -- this is the structural enforcement
mechanism for "no synthesized conclusions" (131B Section 8), not
merely a convention.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class UnifiedQueryResponse:
    query_metadata: dict[str, Any]
    references: tuple[dict[str, Any], ...] = ()
    evidence: tuple[dict[str, Any], ...] = ()
    limitations: tuple[dict[str, Any], ...] = ()
    uncertainty: tuple[dict[str, Any], ...] = ()
    boundary_disclosures: dict[str, Any] = field(default_factory=dict)
    boundary_notes: tuple[str, ...] = ()
    result_status: str = "ok"

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_metadata": self.query_metadata,
            "result_status": self.result_status,
            "references": list(self.references),
            "evidence": list(self.evidence),
            "limitations": list(self.limitations),
            "uncertainty": list(self.uncertainty),
            "boundary_disclosures": self.boundary_disclosures,
            "boundary_notes": list(self.boundary_notes),
            "determinism": {
                "deterministic": True,
                "rule": (
                    "identical repository state plus identical query "
                    "produces identical logical response, except approved "
                    "timestamps (131B Section 13)"
                ),
            },
        }
