# Task Contract

## Task ID

20260621-0902-phase-77a-real-captured-task-readiness-gate

## Title

Phase 77A: Real Captured Task Readiness Gate

## Status

done

## Mode

implementation

## Goal

Add a readiness gate that determines whether PCAE is ready to move from the completed fixture/no-op captured-output pipeline to a real captured task pipeline. This phase must not run a real captured task — it must only assess and report readiness.

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
- No real task package generation
- No new backend capture
- No patch application
- No file modification from backend output
- No commit from backend output
- No push from backend output
- No execution authorization
- No runner-execute real execution

## Acceptance Criteria

- Readiness gate command works (pcae phase real-captured-task-readiness-gate)
- --json works
- --save persists .pcae/real-captured-task-readiness-gates/latest.json
- Show command works (pcae phase real-captured-task-readiness-gate-show --json)
- Missing final lifecycle summary reports blocked_lifecycle_not_closed
- Dirty git status reports blocked_dirty_tree
- Execution not disabled reports blocked_execution_not_disabled
- Runner execution available reports blocked_runner_execution_available
- Current repo reports ready_for_real_task_preparation
- Ready status still reports all safety invariants (execution_allowed=false, etc.)
- Tests cover all scenarios
- python -m pytest tests/test_phase.py passes
- python -m pytest -n auto passes
- pcae health/check/doctor/push check pass
