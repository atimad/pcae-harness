# Task Contract

## Task ID

20260625-2245-88n-permission-broker-design-reconciliation

## Title

88N — Permission Broker Design Reconciliation

## Status

active

## Mode

design_reconciliation

## Goal

Reconcile the Phase 87 permission broker architecture with the concrete Phase 88 explicit preflight layer. Define how a future permission broker should combine scope, backend, mutation/adoption, commit, push, lifecycle, risk, human-review, and task-state evidence into a single decision model while preserving non-execution boundaries and denying by default.

## Allowed Files

- docs/PHASE_88_PERMISSION_BROKER_RECONCILIATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**
- tasks/done/**

## Forbidden Files

- README.md
- src/**
- tests/**
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

- docs/PHASE_88_PERMISSION_BROKER_RECONCILIATION.md exists
- Artifact defines permission broker role and non-role
- Artifact defines broker input/output/decision model
- Artifact documents deny-by-default policy
- Artifact documents known 88M task-finish lifecycle bug
- Artifact recommends 88N.1
- Source files unchanged
- Test files unchanged
- Quick tier passes

## Acceptance Checks

- pcae health
- pcae check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-25T22:45:10.160196+02:00
