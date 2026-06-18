# Task Contract

## Task ID

20260618-0516-70e-task-finish-commit-automation

## Title

70E Task Finish Commit Automation

## Status

active

## Mode

implementation

## Goal

Add --commit MESSAGE to pcae task finish so a task can be validated, finished, staged, and committed in one governed command.

## Allowed Files

- src/pcae/cli.py
- src/pcae/commands/task.py
- src/pcae/core/tasks.py
- tests/test_task.py
- docs/COMMANDS.md
- CHANGELOG.md
- PROJECT_STATUS.md
- tasks/active/**
- tasks/done/**

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

- pcae task finish --commit finishes and commits in one command
- pcae task finish without --commit remains unchanged
- pcae task complete remains backward compatible
- command refuses if unexpected pre-existing changes exist
- command refuses if validation fails unless --skip-checks
- closure commit does not require git commit --no-verify
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-18T05:16:17.873057+02:00
