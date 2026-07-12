# Task Contract

## Task ID

20260712-0946-phase-134e-10-1-final-lifecycle-integration-transaction-span-repair

## Title

Phase 134E.10.1: Final Lifecycle Integration Transaction-Span Repair

## Status

done

## Mode

implementation

## Goal

Repair the BLOCKING architectural finding from 134E.10V: invert control so run_finalization_transaction gates promotion/dispatch via a promote_and_dispatch callback, only invoked after the 7 integrated modules' mandatory pre-promotion stages succeed. Rewire all 4 production entry points. Do not begin 134F or 134E.10.1V.

## Allowed Files

- docs/PHASE_134_FINAL_LIFECYCLE_INTEGRATION_TRANSACTION_SPAN_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- src/pcae/core/finalization_transaction.py
- src/pcae/commands/phase.py
- src/pcae/commands/task.py
- src/pcae/commands/phase_reports.py
- src/pcae/commands/notifications.py
- tests/test_finalization_transaction_134e10.py
- tasks/active/20260712-0946-phase-134e-10-1-final-lifecycle-integration-transaction-span-repair.md

## Forbidden Files

- TBD


## Allowed Zones

- docs
- tasks
- core
- commands
- tests

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

- TBD

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-12T09:46:03.599357+02:00
