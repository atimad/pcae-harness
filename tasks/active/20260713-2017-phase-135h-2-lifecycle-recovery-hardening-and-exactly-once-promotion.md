# Task Contract

## Task ID

20260713-2017-phase-135h-2-lifecycle-recovery-hardening-and-exactly-once-promotion

## Title

Phase 135H.2: Lifecycle Recovery Hardening and Exactly-Once Promotion

## Status

active

## Mode

implementation

## Goal

Independently reproduce the 135H recovery paths, harden recovery so no untrusted candidate can be promoted or dispatched outside the shared finalization transaction, preserve immutable audit evidence, add deterministic public marker-to-checkpoint/receipt reconciliation and consistent paused-task identity semantics, verify exactly-once outcomes, and stop before 135I.

## Allowed Files

- docs/PHASE_135H.2_LIFECYCLE_RECOVERY_HARDENING_AND_EXACTLY_ONCE_PROMOTION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- tasks/active/**
- tasks/paused/**
- tasks/done/**
- src/pcae/**
- tests/**
- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-reports/**
- .pcae/finalization-transactions/**
- .pcae/delivery-receipts/**

## Forbidden Files

- docs/PHASE_135_CANONICAL_LIFECYCLE_TRANSITION_RECORD_CONTRACT.md
- docs/specifications/PFN-001_CANONICAL_PHASE_FINALIZATION_NOTIFICATION_CONTRACT.md
- docs/specifications/PFR-001_CANONICAL_PHASE_REPORT_CONTRACT.md


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

- Exactly-once promotion and exactly-once notification are demonstrated for ordinary, rejected, and recovered completion paths.
- Rejected, partial, and failed candidates remain auditable but never canonical or promoted.
- PFN-001, PFR-001, CLTR-001, runtime capability, and execution availability remain unchanged.

## Acceptance Checks

- pcae health
- pcae check
- pcae doctor task-memory
- pcae push check
- pcae runtime inspect
- python -m compileall -q src tests
- python -m pytest -m "fast_green" -n auto -ra --durations=50

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-13T20:17:21.276268+02:00
