# Task Contract

## Task ID

20260623-0257-phases-80a-80c-lifecycle-advisory-batch

## Title

Phases 80A-80C Lifecycle Advisory Batch

## Status

done

## Mode

implementation

## Goal

Define lifecycle state machine and add read-only advisory lifecycle status and next-step commands. No gate execution, no approval, no mutation.

## Allowed Files

- docs/LIFECYCLE_STATE_MACHINE.md
- src/pcae/lifecycle.py
- src/pcae/commands/lifecycle.py
- src/pcae/cli.py
- tests/test_lifecycle_state_machine.py
- tests/test_lifecycle_status_command.py
- tests/test_lifecycle_next_command.py
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

- Lifecycle state model exists
- Read-only status command exists
- Read-only next command exists
- Commands support JSON
- Commands do not mutate state
- No gate runner or approval commands added

## Acceptance Checks

- python -m pytest tests/test_lifecycle_state_machine.py tests/test_lifecycle_status_command.py tests/test_lifecycle_next_command.py -x

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-23T02:57:27.492592+02:00
