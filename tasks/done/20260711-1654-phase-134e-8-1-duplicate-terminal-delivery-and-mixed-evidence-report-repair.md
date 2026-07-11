# Task Contract

## Task ID

20260711-1654-phase-134e-8-1-duplicate-terminal-delivery-and-mixed-evidence-report-repair

## Title

Phase 134E.8.1 — Duplicate Terminal Delivery and Mixed-Evidence Report Repair

## Status

done

## Mode

implementation

## Goal

Preserve and explain both 134E.8 deliveries; repair the smallest active reporting/finalization/notification boundary so mixed evidence fails closed and ordinary terminal delivery is logically idempotent, without sending external notifications or activating Track 134 delivery subsystems.

## Allowed Files

- CHANGELOG.md
- PROJECT_STATUS.md
- tasks/DECISIONS.md
- tasks/DONE.md
- tasks/active
- tasks/done
- docs/PHASE_134_DUPLICATE_TERMINAL_DELIVERY_MIXED_EVIDENCE_REPAIR.md
- src/pcae/core/phase_reports.py
- src/pcae/commands/notifications.py
- src/pcae/commands/phase.py
- src/pcae/commands/phase_reports.py
- src/pcae/commands/task.py
- tests/test_duplicate_terminal_delivery_mixed_evidence_134e81.py
- tests/test_notification_certification_idempotency.py
- tests/test_phase_113v_n_notification_finalization_repair.py
- tests/test_task_finish_report_trust_notification.py

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

- Incident chronology and field-level evidence comparison identify the exact second-report generation and dispatch paths.
- Internally contradictory or cross-phase reports cannot be complete/consistent or dispatched.
- Repeated finalization and send-report share a transport-neutral logical idempotency boundary.
- Architecture Status inspection remains read-only and runtime remains observe-only with execution unavailable.

## Acceptance Checks

- python -m compileall -q src
- python -m pytest -m fast_green -n auto -ra --durations=100

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-11T16:54:40.533375+02:00
