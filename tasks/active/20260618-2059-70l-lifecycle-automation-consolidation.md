# Task Contract

## Task ID

20260618-2059-70l-lifecycle-automation-consolidation

## Title

70L Lifecycle Automation Consolidation

## Status

active

## Mode

implementation

## Goal

Consolidate, document, and validate the governed lifecycle automation introduced in phases 70A-70K.

## Allowed Files

- docs/COMMANDS.md
- README.md
- tests/test_task.py
- tests/test_push.py
- tests/test_health.py
- tests/test_check.py
- PROJECT_STATUS.md
- CHANGELOG.md
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

- docs describe the current recommended governed lifecycle
- README includes a concise governed lifecycle summary
- pcae health passes
- pcae check passes
- pcae doctor task-memory reports clean
- pcae push check reports expected state
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-18T20:59:21.103877+02:00
