"""Workflow orchestration package (Phase 143O).

Composes 143K-143N infrastructure into deterministic, eight-stage
Interactive Workflow sequencing (``coordinator.WorkflowOrchestrator``) and
the sequencing bookkeeping model that tracks progress
(``models.OrchestrationState``). Implements orchestration only -- no
publication, no CHGR creation, no runtime authority. See
``pcae.interactive_workflow.publication_handoff`` for the separate,
narrower Publication Handoff interface this phase also introduces.
"""

from __future__ import annotations

from pcae.interactive_workflow.orchestration.coordinator import WorkflowOrchestrator
from pcae.interactive_workflow.orchestration.models import (
    ORCHESTRATION_SCHEMA_VERSION,
    STAGE_ORDER,
    OrchestrationStage,
    OrchestrationState,
)

__all__ = [
    "ORCHESTRATION_SCHEMA_VERSION",
    "STAGE_ORDER",
    "OrchestrationStage",
    "OrchestrationState",
    "WorkflowOrchestrator",
]
