# Task Contract

## Task ID

20260618-1947-70i-task-memory-repair

## Title

70I Task Memory Repair

## Status

active

## Mode

implementation

## Goal

Add pcae doctor task-memory --fix so PCAE can repair deterministic task-memory inconsistencies.

## Allowed Files

- src/pcae/commands/task.py
- src/pcae/core/tasks.py
- src/pcae/cli.py
- tests/test_task.py
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**
- tasks/done/**
- tasks/DONE.md
- tasks/TODO.md

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

- --fix repairs done_file_missing_from_done_md
- --fix repairs todo_references_completed_task
- --fix repairs done_status_in_active_folder
- --fix --dry-run shows repairs without mutating
- --fix --json includes structured repair metadata
- unrepairable findings reported but not acted on
- doctor without --fix is unchanged
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-18T19:47:50.623528+02:00
