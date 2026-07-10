# Task Contract

## Task ID

20260710-2252-phase-134b-1-external-notification-investigation-isolation-repair

## Title

Phase 134B.1 — External Notification Investigation & Isolation Repair

## Status

done

## Mode

repair

## Goal

Investigate unexpected external notifications, reproduce the verified test environment inheritance defect safely, isolate ordinary automated tests from live delivery while preserving explicit governed live opt-in and production PFN-001 behavior, document evidence and validation, and finalize cleanly.

## Allowed Files

- tests/conftest.py
- tests/test_external_notification_isolation_134b1.py
- docs/PHASE_134_EXTERNAL_NOTIFICATION_INVESTIGATION_AND_ISOLATION_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DECISIONS.md
- tasks/DONE.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/active/**
- tasks/done/**

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

strict

## Forbidden Changes

- TBD

## Acceptance Criteria

- Ordinary pytest execution cannot inherit live external notification configuration into in-process or subprocess tests.
- Explicit governed live integration testing remains possible through a named opt-in.
- Production notification and PFN-001 behavior remain unchanged.
- Focused reproduction/regression and fast_green pass.

## Acceptance Checks

- pcae check
- git diff --check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-10T22:52:11.830754+02:00
