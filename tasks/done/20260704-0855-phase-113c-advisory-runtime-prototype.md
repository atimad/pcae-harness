# Task Contract

## Task ID

20260704-0855-phase-113c-advisory-runtime-prototype

## Title

Phase 113C: Advisory Runtime Prototype (Observation-Only)

## Status

done

## Mode

implementation

## Goal

Implement the first observation-only Advisory Runtime using the architecture frozen in 113A and the contracts frozen in 113B. Introduce advisory reasoning only -- no authorization, no execution, no enforcement.

## Allowed Files

- src/pcae/core/advisory_runtime.py
- tests/test_advisory_runtime.py
- tests/test_advisory_runtime_architecture.py
- tests/test_advisory_runtime_contract.py
- docs/PCAE_ADVISORY_RUNTIME_PROTOTYPE.md
- docs/PHASE_113_ADVISORY_RUNTIME_PROTOTYPE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/**

## Forbidden Files

- TBD

## Allowed Zones

- TBD

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

TBD

## Forbidden Changes

- TBD

## Acceptance Criteria

- Advisory Runtime implemented
- Advisory Providers implemented
- Runtime Snapshot remains sole input
- Advisory Results produced
- Explainability preserved
- Deterministic aggregation implemented
- Observation-only guarantees maintained
- Runtime state remains Observed
- Execution capability remains unavailable

## Acceptance Checks

- python -m pytest tests/test_advisory_runtime.py tests/test_advisory_runtime_architecture.py tests/test_advisory_runtime_contract.py -n auto -q
- python -m pytest tests/test_*runtime* tests/test_*contract* tests/test_*autonomy* tests/test_*plugin* tests/test_*advisory* -n auto -q
- python -m pytest tests/test_task*.py tests/test_*task* tests/test_*phase* tests/test_phase_reports.py tests/test_phase_reports_cli.py tests/test_notifications.py tests/test_notifications_cli.py tests/test_telegram_notifications.py -n auto -q
- python -m pytest -m fast_green -n auto -q
- pcae health && pcae check && pcae doctor task-memory && pcae push check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-04T08:55:00.000000+00:00
