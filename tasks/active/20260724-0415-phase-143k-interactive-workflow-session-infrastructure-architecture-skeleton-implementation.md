# Task Contract

## Task ID

20260724-0415-phase-143k-interactive-workflow-session-infrastructure-architecture-skeleton-implementation

## Title

Phase 143K: Interactive Workflow Session Infrastructure Architecture & Skeleton Implementation

## Status

active

## Mode

implementation

## Goal

Implement the foundational Session Infrastructure for the Interactive Workflow subsystem defined by Phase 143J's implementation plan, strictly preserving CHGR-001 and IWC-001 v1.1's governance/authority/lifecycle/confirmation contracts. Structural skeleton only: Session domain model, Session Coordinator skeleton, State Machine skeleton, Persistence abstraction (interfaces only), serialization framework, invariant validation framework, error model, package layout, unit tests. No CHGR creation, no workflow execution, no runtime capability expansion.

## Allowed Files

- src/pcae/interactive_workflow/**
- tests/test_iwc_143k_*.py
- docs/PHASE_143K_INTERACTIVE_WORKFLOW_SESSION_INFRASTRUCTURE_ARCHITECTURE_AND_SKELETON_IMPLEMENTATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/TODO.md
- .pcae/policy.toml
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/active/20260724-0254-idle-awaiting-next-governed-phase-after-143j.md
- tasks/done/20260724-0254-idle-awaiting-next-governed-phase-after-143j.md

## Forbidden Files

- TBD


## Allowed Zones

- interactive_workflow
- tests
- docs
- tasks
- policy
- config

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

TBD

## Forbidden Changes

- TBD

## Acceptance Criteria

- Session infrastructure exists (models, identifiers, state representation)
- Repository abstraction exists (interfaces only, no storage technology selected)
- Serialization framework exists
- Validation framework exists
- Error model exists
- Infrastructure tests pass
- No workflow behavior exists (no evidence orchestration, clarification, preview, confirmation, cancellation/expiry/abandonment execution, publication, CHGR creation)
- No authority capability exists
- Runtime remains Observed/observe/unavailable
- CHGR-001, IWC-001, TAMC-001, TAMPC-001 not modified

## Acceptance Checks

- pcae health
- pcae check
- pcae doctor task-memory
- python -m pytest -n auto
- python -m pytest -m fast_green -n auto

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-24T04:15:48.190041+02:00
