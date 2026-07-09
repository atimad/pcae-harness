from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ChangeImpactReport:
    impacted_entities: tuple[dict[str, Any], ...] = ()
    impact_relationships: tuple[dict[str, Any], ...] = ()
    attribution_bundle: tuple[dict[str, Any], ...] = ()
    limitation_bundle: tuple[dict[str, Any], ...] = ()
    boundary_disclosure_bundle: dict[str, Any] = field(default_factory=dict)
    report_metadata: dict[str, Any] = field(default_factory=dict)
    unknowns: tuple[str, ...] = ()
    unavailable: tuple[str, ...] = ()
    incomplete: tuple[str, ...] = ()
    conflicting: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "impacted_entities": list(self.impacted_entities),
            "impact_relationships": list(self.impact_relationships),
            "attribution_bundle": list(self.attribution_bundle),
            "limitation_bundle": list(self.limitation_bundle),
            "boundary_disclosure_bundle": self.boundary_disclosure_bundle,
            "report_metadata": self.report_metadata,
            "unknowns": list(self.unknowns),
            "unavailable": list(self.unavailable),
            "incomplete": list(self.incomplete),
            "conflicting": list(self.conflicting),
            "determinism": {
                "deterministic": True,
                "rule": (
                    "identical Repository Intelligence Query Layer results plus "
                    "identical Change Impact request produce identical logical report"
                ),
            },
        }
