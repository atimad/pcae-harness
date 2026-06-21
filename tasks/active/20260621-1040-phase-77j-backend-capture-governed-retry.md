# Task Contract

## Task ID

20260621-1040-phase-77j-backend-capture-governed-retry

## Title

Phase 77J: Backend Capture Governed Retry

## Status

active

## Mode

implementation

## Goal

Perform exactly one governed backend capture retry using the prepared 300-second timeout and locked backend. Capture output as data only, run mutation guard, and stop before any output intake/review/apply.

## Allowed Files

- src/pcae/cli.py
- src/pcae/commands/phase.py
- tests/test_phase.py
- CHANGELOG.md
- PROJECT_STATUS.md
- tasks/active

## Forbidden

- No backend except locked claude-deepseek
- No output application
- No file modification from backend output
- No commit/push from backend output

## Acceptance Criteria

- Retry command works
- Default/dry-run non-invoking
- All blocking states work
- 10 tests pass
- python -m pytest -n auto passes
- pcae health/check/doctor/push check pass
