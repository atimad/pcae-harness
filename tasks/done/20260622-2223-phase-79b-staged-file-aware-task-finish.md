# Task Contract

## Task ID

20260622-2223-phase-79b-staged-file-aware-task-finish

## Title

Phase 79B Staged-File-Aware Task Finish

## Status

done

## Mode

implementation

## Goal

Add --staged-file-aware flag to pcae task finish --commit that commits only task-finish paths while preserving unrelated pre-existing staged files.

## Allowed Files

- src/pcae/commands/task.py
- src/pcae/cli.py
- tests/test_staged_file_aware_task_finish.py
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

## Acceptance Criteria

- --staged-file-aware flag exists on pcae task finish
- Commits only task-finish paths when flag is active
- Preserves pre-existing staged files
- Blocks protected staged file inclusion
- Never pushes, invokes backend, or runs runner execution

## Acceptance Checks

- python -m pytest tests/test_staged_file_aware_task_finish.py -x

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-22T22:23:53.559530+02:00
