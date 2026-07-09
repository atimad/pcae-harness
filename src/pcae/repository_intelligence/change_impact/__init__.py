"""Deterministic read-only Change Impact reporting prototype (Phase 123E)."""

from __future__ import annotations

from pcae.repository_intelligence.change_impact.change_impact_builder import (
    CHANGE_IMPACT_NON_AUTHORITY_DISCLAIMER,
    ChangeImpactBuilderError,
    build_change_impact_report,
)
from pcae.repository_intelligence.change_impact.change_impact_report import (
    ChangeImpactReport,
)
from pcae.repository_intelligence.change_impact.change_request import (
    ChangeImpactRequest,
)
from pcae.repository_intelligence.change_impact.report_serializer import (
    serialize_change_impact_report,
)
from pcae.repository_intelligence.change_impact.validation import (
    ChangeImpactValidationError,
)

__all__ = [
    "CHANGE_IMPACT_NON_AUTHORITY_DISCLAIMER",
    "ChangeImpactBuilderError",
    "ChangeImpactReport",
    "ChangeImpactRequest",
    "ChangeImpactValidationError",
    "build_change_impact_report",
    "serialize_change_impact_report",
]
