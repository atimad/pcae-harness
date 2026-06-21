# Task Contract

## Task ID

20260621-1020-phase-77h-backend-capture-timeout-policy

## Title

Phase 77H: Backend Capture Timeout Policy

## Status

active

## Mode

implementation

## Goal

Create a governed timeout policy for retrying the 77F timed-out capture. Policy only - no retry.

## Allowed Files

- src/pcae/cli.py
- src/pcae/commands/phase.py
- tests/test_phase.py
- CHANGELOG.md
- PROJECT_STATUS.md
- tasks/active

## Forbidden

- No backend invocation
- No retry
- No backend output capture
- No output application

## Acceptance Criteria

- 9 tests pass
- python -m pytest -n auto passes
- pcae health/check/doctor/push check pass
