# Task: Phase 86I — Phase 85 Integration Tests

## Objective

Add integration tests for the Phase 85 read-only project-intelligence stack.
Validate the six read-only commands together: cross-layer consistency,
read-only behavior, no authority inference, no storage creation.
No new CLI features. No storage. No cache.

## Allowed Files

- tests/test_phase85_integration.py
- docs/PHASE_85_READ_ONLY_STACK_INTEGRATION_TESTS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/86i-phase-85-integration-tests.md
- tasks/completed/86h-read-only-project-state-snapshot-cli.md
- src/** only if small bugfix exposed by integration tests

## Forbidden Files

- README.md
- docs/REAL_CAPTURED_TASKS.md
- .pcae/**
- .githooks/**
- existing Phase 85 design docs
- existing 86C–86H prototype artifacts
- pyproject.toml

## Acceptance Criteria

- Integration tests cover all six read-only commands
- Cross-layer consistency verified
- Read-only/no-storage behavior verified
- No authority inference verified
- Existing tests still pass
- README.md unchanged

## Status

- [x] Created
- [x] In Progress
- [x] Complete
