# Task Contract

## Task ID

20260726-1747-phase-145g-1-interactive-workflow-cli-command-surface-completion-and-readiness-construction-repair

## Title

Phase 145G.1: Interactive Workflow CLI Command-Surface Completion and Readiness Construction Repair

## Status

active

## Mode

implementation

## Goal

Implement the five missing decision-session commands (evidence/clarify/preview/confirm/cancel) and repair readiness construction (IWPC-REQ-024), by adding a narrow persisted orchestration-state store and extending SessionApplicationService, without redesigning Interactive Workflow architecture or modifying frozen contract text. Runtime remains Observed/observe/unavailable.

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- src/pcae/commands/decision_session.py
- src/pcae/cli.py
- src/pcae/interactive_workflow/application/session_service.py
- src/pcae/interactive_workflow/application/publication_service.py
- src/pcae/interactive_workflow/application/errors.py
- src/pcae/interactive_workflow/errors.py
- src/pcae/interactive_workflow/orchestration/coordinator.py
- src/pcae/interactive_workflow/persistence/filesystem_orchestration_store.py
- tests/test_phase_145g1_decision_session_cli_repair.py
- docs/PHASE_145G1_INTERACTIVE_WORKFLOW_CLI_COMMAND_SURFACE_COMPLETION_AND_READINESS_CONSTRUCTION_REPAIR.md
- docs/COMMANDS.md
- src/pcae/core/docs.py
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- .pcae/policy.toml

## Forbidden Files

- docs/contracts/**
- src/pcae/governance/publication/**
- src/pcae/interactive_workflow/orchestration/models.py
- src/pcae/interactive_workflow/publication_handoff/**


## Allowed Zones

- TBD

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

- TBD

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-26T17:47:45.353688+02:00
