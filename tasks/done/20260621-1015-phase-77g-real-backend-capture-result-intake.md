# Task Contract

## Task ID

20260621-1015-phase-77g-real-backend-capture-result-intake

## Title

Phase 77G: Real Backend Capture Result Intake

## Status

done

## Mode

implementation

## Goal

Add a result intake command for real backend capture results. Classifies capture outcomes. Never invokes backend, retries capture, or applies output.

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
- No backend output capture in this phase
- No output application
- No commit/push from backend output

## Acceptance Criteria

- Intake command works
- All outcome classifications work
- Safety invariants enforced
- 11 tests pass
- python -m pytest -n auto passes
