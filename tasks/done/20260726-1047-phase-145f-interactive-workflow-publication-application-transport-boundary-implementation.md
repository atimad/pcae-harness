# Task Contract

## Task ID

20260726-1047-phase-145f-interactive-workflow-publication-application-transport-boundary-implementation

## Title

Phase 145F: Interactive Workflow + Publication Application/Transport Boundary Implementation

## Status

done

## Mode

implementation

## Goal

Implement the application/service boundary connecting Interactive Workflow (SessionRepository, FilesystemSessionRepository 145D) to Publication (FilesystemPendingReadinessStore 145E, PublicationCoordinator) per IWPC-001 v1.1 exactly. No CLI, no transport adapter, no engineering execution, no contract text changes.

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- src/pcae/interactive_workflow/application/**
- tests/test_phase_145f_application_service_boundary.py
- docs/PHASE_145F_INTERACTIVE_WORKFLOW_PUBLICATION_APPLICATION_TRANSPORT_BOUNDARY_IMPLEMENTATION.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- .pcae/policy.toml

## Forbidden Files

- docs/contracts/INTERACTIVE_WORKFLOW_PUBLICATION_CLI_TRANSPORT_CONTRACT.md
- docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md
- docs/contracts/PUBLICATION_EXECUTION_CONTRACT.md
- docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md


## Allowed Zones

- config
- docs
- tasks
- interactive_workflow
- tests
- policy

## Forbidden Zones

- commands
- cli
- governance
- cltr

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

advisory

## Forbidden Changes

- TBD

## Acceptance Criteria

- TBD

## Acceptance Checks

- pcae health
- pcae check
- python -m pytest tests/test_phase_145f_application_service_boundary.py -q
- python -m pytest tests/test_phase_145d_session_repository_filesystem_implementation.py tests/test_phase_145e_pending_readiness_store_filesystem_implementation.py tests/test_phase_144c_publication_coordinator.py -q

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-26T10:47:14.365496+02:00
