# Task Contract

## Task ID

20260625-2303-88n-1-task-finish-tracked-file-robustness

## Title

88N.1 — Task Finish Tracked-File Robustness

## Status

done

## Mode

lifecycle_bugfix

## Goal

Fix pcae task finish so it handles untracked active task files safely without pathspec failure or partial finish state. Add regression tests.

## Allowed Files

- src/pcae/commands/task.py
- tests/test_staged_file_aware_task_finish.py
- docs/PHASE_88_TASK_FINISH_TRACKED_FILE_ROBUSTNESS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**
- tasks/done/**

## Forbidden Files

- README.md
- src/pcae/core/**
- docs/REAL_CAPTURED_TASKS.md
- .pcae/**


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

## Acceptance Criteria

- pcae task finish succeeds with tracked active task file
- pcae task finish succeeds with untracked active task file
- No pathspec failure on untracked active task finish
- Regression tests pass
- Quick tier passes

## Acceptance Checks

- pcae health
- pcae check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-25T23:03:52.200250+02:00
