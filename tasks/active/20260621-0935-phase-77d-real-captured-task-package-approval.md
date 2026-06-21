# Task Contract

## Task ID

20260621-0935-phase-77d-real-captured-task-package-approval

## Title

Phase 77D: Real Captured Task Package Approval

## Status

active

## Mode

implementation

## Goal

Add an approval artifact for the real captured task package dry-run. The approval should authorize a future backend capture preflight, not backend invocation now. This phase must not send the package and must not invoke any backend.

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
- No new backend capture
- No patch application from backend output
- No file modification from backend output
- No commit from backend output
- No push from backend output
- No execution authorization
- No runner-execute real execution
- Do not create docs/REAL_CAPTURED_TASKS.md

## Acceptance Criteria

- Package approval command works
- --json works, --save persists
- Show command works
- Missing dry-run reports missing_package_dry_run
- Package not ready reports package_not_ready
- Digest mismatch reports digest_mismatch
- Dirty tree, audit warnings, execution/runner blocks all work
- Default reports ready_for_approval_request
- --approve creates approved artifact
- Approved binds package/contract digests
- All safety invariants enforced
- 15 tests pass
- python -m pytest -n auto passes
- pcae health/check/doctor/push check pass
