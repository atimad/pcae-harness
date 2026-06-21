# Task Contract

## Task ID

20260621-0915-phase-77b-real-captured-task-contract-preparation

## Title

Phase 77B: Real Captured Task Contract Preparation

## Status

active

## Mode

implementation

## Goal

Prepare the first real captured task contract, but do not create a backend task package, do not invoke a backend, and do not capture real backend output yet. The contract defines the governance boundaries for a future real captured task.

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
- No backend task package generation
- No new backend capture
- No patch application from backend output
- No file modification from backend output
- No commit from backend output
- No push from backend output
- No execution authorization
- No runner-execute real execution

## Acceptance Criteria

- Contract preparation command works
- --json works
- --save persists .pcae/real-captured-task-contracts/latest.json
- Show command works
- Missing readiness gate reports blocked_readiness_not_ready
- Dirty git status reports blocked_dirty_tree
- Execution disabled false reports blocked_execution_not_disabled
- Runner execution available reports blocked_runner_execution_available
- Clean repo prepares a documentation-only contract
- All safety invariants enforced
- 10 tests pass
- python -m pytest -n auto passes
- pcae health/check/doctor/push check pass
