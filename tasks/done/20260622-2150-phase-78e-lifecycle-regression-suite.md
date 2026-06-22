# Task Contract

## Task ID

20260622-2150-phase-78e-lifecycle-regression-suite

## Title

Phase 78E Lifecycle Regression Suite

## Status

done

## Mode

implementation

## Goal

Add regression tests protecting the major invariants proven by the completed backend-created output adoption lifecycle (77J-77V.1).

## Allowed Files

- tests/test_lifecycle_regression.py
- tests/test_phase.py
- CHANGELOG.md
- PROJECT_STATUS.md
- tasks/active
- tasks/active/*

## Forbidden Files

- docs/REAL_CAPTURED_TASKS.md
- docs/ROADMAP.md
- docs/BACKEND_OUTPUT_LIFECYCLE_RETROSPECTIVE.md
- docs/LIFECYCLE_COMMAND_CONSOLIDATION_PLAN.md
- docs/ADOPTION_LIFECYCLE_SUMMARY.md

## Allowed Zones

- TBD

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

strict

## Forbidden Changes

- docs/REAL_CAPTURED_TASKS.md modification
- Backend invocation
- Lifecycle state machine implementation

## Acceptance Criteria

- Lifecycle regression tests exist and pass
- Tests cover key invariants from 77J-77V.1
- Tests are deterministic and do not require backend availability
- No modification to docs/REAL_CAPTURED_TASKS.md

## Acceptance Checks

- python -m pytest tests/test_lifecycle_regression.py -x

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-22T21:50:52.451570+02:00
