# Task Contract

## Task ID

20260621-0945-phase-77e-real-captured-task-backend-capture-preflight

## Title

Phase 77E: Real Captured Task Backend Capture Preflight

## Status

done

## Mode

implementation

## Goal

Add a backend capture preflight artifact for the approved real captured task package. This phase should determine whether PCAE may proceed to a future explicit backend capture phase. Must not invoke claude-deepseek and must not send the package.

## Allowed Files

- src/pcae/cli.py
- src/pcae/commands/phase.py
- tests/test_phase.py
- CHANGELOG.md
- PROJECT_STATUS.md
- tasks/active

## Forbidden

- No backend invocation
- No prompt execution
- No package send
- No backend output capture
- No patch application from backend output
- No file modification from backend output
- No execution authorization
- Do not create docs/REAL_CAPTURED_TASKS.md

## Acceptance Criteria

- Preflight command works
- --json, --save, show all work
- Blocks on missing approval, unapproved, digest mismatch, dirty tree, audit warnings, execution/runner/lock/backend issues
- Ready reports backend_capture_allowed_in_future_phase=true
- All present-tense safety invariants remain false
- 10 tests pass
- python -m pytest -n auto passes
- pcae health/check/doctor/push check pass
