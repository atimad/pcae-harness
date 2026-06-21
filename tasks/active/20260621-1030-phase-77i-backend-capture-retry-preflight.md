# Task Contract

## Task ID

20260621-1030-phase-77i-backend-capture-retry-preflight

## Title

Phase 77I: Backend Capture Retry Preflight

## Status

active

## Mode

implementation

## Goal

Create a governed backend capture retry preflight artifact. Validates retry eligibility under the prepared 300s timeout policy. Must not perform the retry.

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

- Retry preflight command works
- All blocking states work
- Prepared preflight reports ready_for_retry
- 9 tests pass
- python -m pytest -n auto passes
- pcae health/check/doctor/push check pass
