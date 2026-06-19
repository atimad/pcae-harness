# Task Contract

## Task ID

20260619-1431-phase-71q-1-partial-task-finish-recovery

## Title

Phase 71Q.1 Partial Task Finish Recovery

## Status

done

## Mode

implementation

## Goal

Add a governed recovery path for partial task finish closure states where task movement completed but the closure commit failed.

## Allowed Files

- src/pcae/cli.py
- src/pcae/commands/task.py
- src/pcae/core/tasks.py
- tests/test_task.py
- CHANGELOG.md
- PROJECT_STATUS.md
- tasks/active/*71q-1*.md
- tasks/active/*71q1*.md

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

TBD

## Forbidden Changes

- TBD

## Acceptance Criteria

- Recovery command detects a partial task finish state.
- Dry-run reports recovery plan without mutating.
- Recovery commits only closure files and refuses unrelated dirty files.
- Recovery refuses ambiguous multiple closure transitions.
- JSON output works for dry-run, success, and refusal.

## Acceptance Checks

- python -m pytest tests/test_task.py
- python -m pytest -n auto
- pcae health
- pcae check
- pcae doctor task-memory
- pcae push check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-19T14:31:39.606508+02:00
