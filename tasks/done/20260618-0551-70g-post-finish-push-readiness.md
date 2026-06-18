# Task Contract

## Task ID

20260618-0551-70g-post-finish-push-readiness

## Title

70G Post-Finish Push Readiness

## Status

done

## Mode

implementation

## Goal

Teach pcae push check to distinguish invalid no-active-task drift from a valid post-finish closure state.

## Allowed Files

- src/pcae/commands/push.py
- tests/test_push.py
- PROJECT_STATUS.md
- CHANGELOG.md
- docs/COMMANDS.md
- tasks/active/**

## Forbidden Files

- TBD


## Allowed Zones

- TBD

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

advisory

## Forbidden Changes

- TBD

## Acceptance Checks

- pcae push check passes normal active-task ready state
- pcae push check passes valid post-finish closure state
- pcae push check refuses dirty tree
- pcae push check refuses arbitrary no-active-task drift
- pcae push check --json reports mode clearly
- python -m pytest tests/test_push.py passes
- python -m pytest -n auto passes
- pcae health passes
- pcae check passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-18T05:51:11.352695+02:00
