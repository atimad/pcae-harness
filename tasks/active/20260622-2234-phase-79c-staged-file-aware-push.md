# Task Contract

## Task ID

20260622-2234-phase-79c-staged-file-aware-push

## Title

Phase 79C Staged-File-Aware Push

## Status

active

## Mode

implementation

## Goal

Add --staged-file-aware flag to pcae push that pushes approved commits while preserving unrelated pre-existing staged files. Blocks if protected staged files appear in unpushed commit contents.

## Allowed Files

- src/pcae/commands/push.py
- src/pcae/cli.py
- tests/test_staged_file_aware_push.py
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

- --staged-file-aware flag exists on pcae push
- Pushes approved commits while preserving protected staged files
- Blocks if protected files in unpushed commits
- Blocks force push
- Never invokes backend or runs runner execution

## Acceptance Checks

- python -m pytest tests/test_staged_file_aware_push.py -x

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-22T22:34:00.981751+02:00
