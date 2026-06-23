# Task Contract

## Task ID

20260623-0329-phase-80f-lifecycle-final-summary-command

## Title

Phase 80F Lifecycle Final Summary Command

## Status

done

## Mode

implementation

## Goal

Add a read-only lifecycle final summary command that aggregates status, gates, approvals, blockers, safety flags, and command capabilities in one report.

## Allowed Files

- src/pcae/lifecycle.py
- src/pcae/commands/lifecycle.py
- src/pcae/cli.py
- tests/test_lifecycle_summary_command.py
- CHANGELOG.md
- PROJECT_STATUS.md
- tasks/active
- tasks/active/*

## Forbidden Files

- docs/REAL_CAPTURED_TASKS.md

## Allowed Zones

- TBD

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

strict

## Forbidden Changes

- docs/REAL_CAPTURED_TASKS.md modification
- Backend invocation
- Gate execution
- execution_authorized=true

## Acceptance Criteria

- Summary command exists and supports JSON
- Read-only by default
- Aggregates status, gates, safety flags, capabilities
- execution_authorized=false always
- No gate execution, approval, or backend invocation

## Acceptance Checks

- python -m pytest tests/test_lifecycle_summary_command.py -x

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-23T03:29:48.361926+02:00
