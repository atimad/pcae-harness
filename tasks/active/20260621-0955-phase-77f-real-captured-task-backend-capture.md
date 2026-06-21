# Task Contract

## Task ID

20260621-0955-phase-77f-real-captured-task-backend-capture

## Title

Phase 77F: Real Captured Task Backend Capture

## Status

active

## Mode

implementation

## Goal

Perform the first real captured task backend capture using the approved package and locked backend, while proving PCAE does not allow backend output to mutate the repository. Default/--dry-run validates gates without invocation. --execute invokes locked backend.

## Allowed Files

- src/pcae/cli.py
- src/pcae/commands/phase.py
- tests/test_phase.py
- CHANGELOG.md
- PROJECT_STATUS.md
- tasks/active

## Forbidden

- No output application
- No file modification from backend output
- No commit/push from backend output
- No runner-execute real execution
- Do not create docs/REAL_CAPTURED_TASKS.md from backend output

## Acceptance Criteria

- Capture command works
- Default/dry-run non-invoking
- All blocking states work
- Synthetic tests pass
- No output application/commit/push
- 12 tests pass
- python -m pytest -n auto passes
