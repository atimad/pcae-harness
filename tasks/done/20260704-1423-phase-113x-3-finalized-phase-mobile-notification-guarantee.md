# Task Contract

## Task ID

20260704-1423-phase-113x-3-finalized-phase-mobile-notification-guarantee

## Title

Phase 113X.3: Finalized Phase Mobile Notification Guarantee

## Status

done

## Mode

implementation

## Goal

Fix the naive lexicographic backward-pointing recommended-next-phase heuristic (wrongly flags 113D as before 113X.2) so valid branch transitions are not marked partial. Add a finalization notification guarantee: complete reports send normal Telegram notification; finalized-but-partial reports (canonical latest.* written, e.g. via --allow-partial-report) send a clearly labeled warning notification instead of silence; quarantined/blocked reports remain silent (113X.1 semantics unchanged); all outcomes (attempted/sent/skipped_with_reason/failed_with_reason) are recorded and visible in the report.

## Allowed Files

- src/pcae/core/phase_reports.py
- src/pcae/commands/phase.py
- src/pcae/core/notifications.py
- tests/test_phase_report_trust_hard_fail.py
- tests/test_finalization_notification_guarantee.py
- docs/PHASE_113X3_FINALIZED_PHASE_MOBILE_NOTIFICATION_GUARANTEE.md
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

- 113X.2 -> 113D is not marked backward/partial by lexicographic comparison
- Complete finalized report still sends normal Telegram notification
- Partial but finalized (canonical-written) report sends a clearly labeled warning notification
- Partial report is never sent as a normal final completion report
- Telegram skip/failure is recorded with an explicit reason, visible in the report
- 113X.1 quarantine behavior (blocked reports never write latest.*, remain silent) is intact
- 113X.2 identity-conflict blocker behavior is intact

## Acceptance Checks

- python -m pytest tests/test_finalization_notification_guarantee.py -n auto -q
- python -m pytest tests/test_finalization_gate_enforcement.py tests/test_canonical_phase_identity_repair.py tests/test_phase_reports.py tests/test_phase_report_trust_hard_fail.py -n auto -q
- pcae check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-04T14:23:02.563658+02:00
