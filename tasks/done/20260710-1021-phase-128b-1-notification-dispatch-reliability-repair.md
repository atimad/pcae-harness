# Task Contract

## Task ID

20260710-1021-phase-128b-1-notification-dispatch-reliability-repair

## Title

Phase 128B.1 Notification Dispatch Reliability Repair

## Status

done

## Mode

implementation

## Goal

Repair the missing Telegram/notification dispatch path in pcae phase-report create (the documented recovery command when pcae phase complete is rejected by the repository transition validator, as in 128B) and the duplicate-dispatch gap in pcae notify send-report --latest. Minimal, targeted tooling repair; no Repository Intelligence, Historical Memory, or runtime capability changes.

## Allowed Files

- src/pcae/commands/phase_reports.py
- src/pcae/commands/notifications.py
- tests/test_phase_reports.py
- docs/PHASE_128B1_NOTIFICATION_DISPATCH_RELIABILITY_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/20260710-1021-phase-128b-1-notification-dispatch-reliability-repair.md

## Forbidden Files

- TBD


## Allowed Zones

- commands
- tests
- docs
- tasks

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

- Root-caused why pcae phase-report create (the primary 128B recovery path) never dispatched a Telegram notification for a trust-complete report
- Repaired the missing dispatch path using the existing certification/idempotency-marker mechanism, without redesigning the notification/reporting architecture
- Every trusted canonical report dispatches exactly one notification; duplicate dispatch is prevented across pcae phase complete, pcae phase-report create, and pcae notify send-report --latest
- Dispatch always occurs after the canonical report is written and trust-assessed; failures are observable in command output; untrusted reports never dispatch
- New regression tests cover normal completion, phase-report create path, recovery-after-rejection, duplicate prevention, ordering, failed-dispatch visibility, trusted dispatch, and untrusted no-dispatch
- No Repository Intelligence, Historical Memory, schema, or runtime-capability files changed; runtime remains Observed/observe/execution-unavailable

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-10T10:21:43.143356+02:00
