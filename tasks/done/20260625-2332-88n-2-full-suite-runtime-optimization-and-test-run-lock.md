# Task Contract

## Task ID

20260625-2332-88n-2-full-suite-runtime-optimization-and-test-run-lock

## Title

88N.2 — Full Suite Runtime Optimization and Test-Run Lock

## Status

done

## Mode

test_governance

## Goal

Profile test runtime, document validation tiers, and add pcae doctor test-run preflight to prevent overlapping expensive pytest runs.

## Allowed Files

- src/pcae/commands/task.py
- src/pcae/cli.py
- tests/test_doctor_test_run.py
- docs/PHASE_88_FULL_SUITE_RUNTIME_OPTIMIZATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- pyproject.toml
- tasks/active/**
- tasks/done/**

## Forbidden Files

- README.md
- docs/REAL_CAPTURED_TASKS.md
- .pcae/**


## Allowed Zones

- TBD

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

advisory

## Forbidden Changes

- TBD

## Acceptance Criteria

- pcae doctor test-run reports clear_to_run=true when no active test run
- pcae doctor test-run reports clear_to_run=false when active test run detected
- Tests for doctor test-run pass
- Validation tiers documented
- Quick tier passes

## Acceptance Checks

- pcae health
- pcae check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-25T23:32:47.063702+02:00
