"""Clarification infrastructure (IWC-001 v1.1 §9, Phase 143M).

Request/response registration, ordering, and history for a single
Decision Session's clarification exchanges, with a structural,
synchronous rejection of any attempt to classify a clarification as a
recommendation, persuasion, approval, authorization, or decision
(IWC-001 v1.1 §9.1's four-act boundary; IWC-REQ-093 through IWC-REQ-095).
Contains no recommendation, persuasion, prioritization, decision-making,
or session-transition capability.
"""

from __future__ import annotations

from pcae.interactive_workflow.clarification.controller import ClarificationController
from pcae.interactive_workflow.clarification.models import (
    CLARIFICATION_SCHEMA_VERSION,
    Clarification,
    ClarificationState,
    validate_classification_tag,
)

__all__ = [
    "CLARIFICATION_SCHEMA_VERSION",
    "Clarification",
    "ClarificationState",
    "validate_classification_tag",
    "ClarificationController",
]
