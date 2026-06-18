# Task Contract

## Task ID

20260618-0502-70d-task-contract-ergonomics

## Title

70D Task Contract Ergonomics

## Status

active

## Mode

implementation

## Goal

Extend pcae task new so a complete task contract can be created in one command, using the same contract fields already supported by pcae task update and create_task_contract().

## Allowed Files

- src/pcae/cli.py
- src/pcae/commands/task.py
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

- pcae task new creates complete contract in one command
- All relevant flags from pcae task update available on pcae task new
- Session auto-refreshed after task creation
- Existing pcae task new TITLE behavior unchanged
- pcae task update behavior unchanged
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-18T05:02:01.712461+02:00
