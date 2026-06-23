# Task Contract

## Task ID

20260623-0311-phase-80d-lifecycle-gate-runner-dry-run

## Title

Phase 80D Lifecycle Gate Runner Dry-Run

## Status

done

## Mode

implementation

## Goal

Add a lifecycle gate runner dry-run command that evaluates gate readiness without executing. --dry-run required, no real gate execution, no approval, no mutation.

## Allowed Files

- src/pcae/lifecycle.py
- src/pcae/commands/lifecycle.py
- src/pcae/cli.py
- tests/test_lifecycle_gate_runner_dry_run.py
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
- Approval execution

## Acceptance Criteria

- Dry-run gate runner command exists
- --dry-run is required
- JSON output supported
- No gate execution or approval occurs
- No backend invocation

## Acceptance Checks

- python -m pytest tests/test_lifecycle_gate_runner_dry_run.py -x

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-23T03:11:07.444140+02:00
