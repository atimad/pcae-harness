"""Boundary disclosure bundle: reuse the real, frozen nine-field schema verbatim (131D Section 6-7).

131C independently discovered that 131B's six-item conceptual boundary
list does not name-match the real, already-frozen, already-used
``boundary_disclosure.schema.json`` (nine required boolean-const
fields). 131D's resolution -- reuse the existing schema verbatim,
never invent a new one -- is implemented here by importing the exact
same ``BOUNDARY_DISCLOSURES``/``BOUNDARY_NOTES`` constants Track 130's
own ``integration_builder.py`` already defines, guaranteeing byte-for-
byte reuse rather than a second, potentially-drifting definition.
"""

from __future__ import annotations

from typing import Any

from pcae.repository_intelligence.cross_artifact_integration.integration_builder import (
    BOUNDARY_DISCLOSURES,
    BOUNDARY_NOTES,
)

UNIFIED_QUERY_BOUNDARY_NOTES: tuple[str, ...] = tuple(BOUNDARY_NOTES) + (
    "This Unified Repository Intelligence Query response is a derivative "
    "access layer over already-authoritative Repository Intelligence "
    "artifacts; it introduces no new evidence, performs no reasoning, "
    "ranking, recommendation, Decision Evaluation, or execution.",
)


def unified_query_boundary_disclosures() -> dict[str, Any]:
    """Return the real nine-field boundary disclosure object, unmodified."""
    return dict(BOUNDARY_DISCLOSURES)


def unified_query_boundary_notes() -> list[str]:
    return list(UNIFIED_QUERY_BOUNDARY_NOTES)
