# Task Contract

## Task ID

20260724-0901-phase-143n-interactive-workflow-confirmation-preview-infrastructure-implementation

## Title

Phase 143N: Interactive Workflow Confirmation & Preview Infrastructure Implementation

## Status

done

## Mode

implementation

## Goal

Implement the Preview and Confirmation infrastructure defined by IWC-001 v1.1 on top of Session Infrastructure (143K), Transition Engine (143L), and Evidence/Clarification/Audit (143M): Preview Builder, immutable Preview model, deterministic Preview Digest generation, preview validation, Confirmation Controller, immutable ConfirmationRequest/ConfirmationResponse models, replay protection, stale-preview detection, serialization framework, infrastructure error hierarchy, comprehensive unit/regression tests. No session orchestration, publication handoff, CHGR creation, or execution capability. Runtime capability unchanged.

## Allowed Files

- src/pcae/interactive_workflow/**
- tests/test_iwc_143n_*.py
- docs/PHASE_143N_INTERACTIVE_WORKFLOW_CONFIRMATION_AND_PREVIEW_INFRASTRUCTURE_IMPLEMENTATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/TODO.md
- tasks/done/**
- .pcae/policy.toml
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

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

- Preview Builder and immutable Preview model exist
- Preview Digest generation is deterministic
- Preview validation exists (schema version, missing/duplicate refs, digest consistency)
- Confirmation Controller and immutable ConfirmationRequest/ConfirmationResponse models exist
- Replay protection exists
- Stale-preview detection exists
- All infrastructure models are immutable
- Infrastructure tests pass
- Runtime remains unchanged
- No governance workflow capability exists

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-24T09:01:02.365130+02:00
