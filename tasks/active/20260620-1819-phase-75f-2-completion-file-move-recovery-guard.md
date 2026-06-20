# Task Contract

## Task ID

20260620-1819-phase-75f-2-completion-file-move-recovery-guard

## Title

Phase 75F.2: Completion File Move Recovery Guard

## Status

active

## Mode

implementation

## Goal

Add detection and recovery for task files in tasks/done that still have internal status=active. Enhance pcae doctor task-memory with --fix-status --dry-run/--fix-status.

## Allowed Files

- src/pcae/core/tasks.py
- src/pcae/cli.py
- tests/test_task.py
- CHANGELOG.md
- PROJECT_STATUS.md
- tasks/active
- tasks/active/*

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

- TBD

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-20T18:19:04.066619+02:00
