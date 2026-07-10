"""Repository Intelligence Service response model (132D Section 6).

A closed shape: request metadata, per-family content, composition
metadata, limitations, uncertainty, and boundary disclosures -- plus,
for composite requests only, a tuple of independently-composed inner
responses. ``composition_metadata`` is structurally separate from any
per-element ``provenance`` dict (132D Section 6's own concrete
resolution of 132C's composition-metadata-boundary finding): it
records only which Unified Query calls were made, for which family,
with what outcome -- never a claim about entity content.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ServiceResponse:
    request_metadata: dict[str, Any]
    families: dict[str, dict[str, Any]] = field(default_factory=dict)
    composition_metadata: tuple[dict[str, Any], ...] = ()
    limitations: tuple[dict[str, Any], ...] = ()
    uncertainty: tuple[dict[str, Any], ...] = ()
    boundary_disclosures: dict[str, Any] = field(default_factory=dict)
    boundary_notes: tuple[str, ...] = ()
    result_status: str = "ok"
    composite_responses: tuple["ServiceResponse", ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_metadata": self.request_metadata,
            "result_status": self.result_status,
            "families": self.families,
            "composition_metadata": list(self.composition_metadata),
            "limitations": list(self.limitations),
            "uncertainty": list(self.uncertainty),
            "boundary_disclosures": self.boundary_disclosures,
            "boundary_notes": list(self.boundary_notes),
            "composite_responses": [r.to_dict() for r in self.composite_responses],
            "determinism": {
                "deterministic": True,
                "rule": (
                    "identical repository state plus identical service "
                    "request produces identical logical response, except "
                    "approved timestamps (132B Section 13)"
                ),
            },
        }
