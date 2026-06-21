# Task Contract

## Task ID

20260621-0920-phase-77c-real-captured-task-package-dry-run

## Title

Phase 77C: Real Captured Task Package Dry-Run

## Status

active

## Mode

implementation

## Goal

Create a dry-run package envelope for REAL-CAPTURED-TASK-001 without sending it to any backend. This phase may build/package the task artifact for review, but must not invoke claude-deepseek, must not capture backend output, and must not allow execution.

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
- No backend task package send
- No new backend capture
- No patch application from backend output
- No file modification from backend output
- No commit from backend output
- No push from backend output
- No execution authorization
- No runner-execute real execution
- Do not create docs/REAL_CAPTURED_TASKS.md yet

## Acceptance Criteria

- Package dry-run command works
- --json works
- --save persists .pcae/real-captured-task-package-dry-runs/latest.json
- Show command works
- Missing contract reports blocked_contract_missing
- Contract not prepared reports blocked_contract_not_prepared
- Dirty git status reports blocked_dirty_tree
- Execution disabled false reports blocked_execution_not_disabled
- Runner execution available reports blocked_runner_execution_available
- Current repo reports package_dry_run_status=ready
- Ready package includes contract_id REAL-CAPTURED-TASK-001
- Ready package reports all safety invariants
- 10 tests pass
- python -m pytest -n auto passes
- pcae health/check/doctor/push check pass
