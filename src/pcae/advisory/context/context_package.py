from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

#: Restated at package level so every delivered package discloses,
#: without exception, that it is context only (122B S6.2/S11, 122D
#: S11). This is additive to whatever boundary disclosures/disclaimers
#: the source Query Result already carried -- it never replaces them.
NON_AUTHORITY_DISCLAIMER = (
    "This Repository Intelligence Advisory context package is context "
    "only. It is not Evidence, not Repository State, and not a "
    "Decision Evaluation output. It confers no authority and performs "
    "no reasoning or decision making."
)


@dataclass(frozen=True)
class RepositoryIntelligenceContextPackage:
    """The bounded, deterministic, provenance-preserving Repository
    Intelligence context assembled by the 122E Advisory Context
    Builder (122A S6 / 122B S8 / 122D S7).

    Structurally independent from the frozen 115W
    ``pcae.core.advisory_context_package.AdvisoryContextPackage`` --
    this package decides no placement into that type's 15 sections
    (122B S8, 122C S17-18, 122D S7/S16). A future, explicit
    115W-contract amendment or extension phase is required before any
    section placement decision is made.
    """

    selected_repository_intelligence: tuple[dict[str, Any], ...]
    attribution_bundle: tuple[dict[str, Any], ...]
    limitation_bundle: tuple[dict[str, Any], ...]
    boundary_disclosure_bundle: dict[str, Any]
    context_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_repository_intelligence": list(
                self.selected_repository_intelligence
            ),
            "attribution_bundle": list(self.attribution_bundle),
            "limitation_bundle": list(self.limitation_bundle),
            "boundary_disclosure_bundle": self.boundary_disclosure_bundle,
            "context_metadata": self.context_metadata,
            "determinism": {
                "deterministic": True,
                "rule": (
                    "identical Query Layer result(s) plus identical advisory "
                    "context request produces identical logical advisory "
                    "context package"
                ),
            },
        }
