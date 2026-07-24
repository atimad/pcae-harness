# Task Contract

## Task ID

20260724-1701-phase-144c-publication-coordinator-implementation

## Title

Phase 144C: Publication Coordinator Implementation

## Status

active

## Mode

implementation

## Goal

Implement PublicationCoordinator exactly as specified by PEC-001 v1.0 (Publication Execution Contract): the sole production owner of Publication Execution, external to interactive_workflow/**, cltr/**, and the PCAE phase-lifecycle tree. No CLI, no workflow changes, no runtime capability changes.

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- src/pcae/governance/publication/**
- tests/test_phase_144c_publication_coordinator.py
- docs/PHASE_144C_PUBLICATION_COORDINATOR_IMPLEMENTATION.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- .pcae/policy.toml

## Forbidden Files

- docs/contracts/PUBLICATION_EXECUTION_CONTRACT.md
- docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md
- docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md
- docs/contracts/TYPED_AUTHORITY_MODEL_CONSUMPTION_CONTRACT.md
- docs/contracts/TYPED_AUTHORITY_MODEL_PRODUCTION_CONSUMPTION_CONTRACT.md


## Allowed Zones

- governance
- tests
- docs
- tasks
- policy
- config

## Forbidden Zones

- interactive_workflow
- cltr
- commands
- core

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

strict

## Forbidden Changes

- No CLI command implementation
- No automatic publication / publish-when-ready behavior
- No delegated authorization tokens
- No runtime capability changes
- No Interactive Workflow redesign
- No lifecycle redesign
- No contract text changes

## Acceptance Criteria

- PublicationCoordinator implemented external to interactive_workflow/**, cltr/**, and the PCAE phase-lifecycle tree
- Cannot be reached, and performs no write, absent a verified Publication Authorization Event
- Rejects Replay at its single entry point
- Atomic write: identity assignment and provenance/integrity capture occur within the same operation as the write itself
- No responsibility duplicated or left unowned
- Runtime posture remains Observed/observe/unavailable
- Every failure scenario terminates deterministically with no partial CHGR created
- 143P's Interactive Workflow certification remains valid and unaffected

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest passes (full suite, including 143K-143P regression)

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-24T17:01:26.620199+02:00
