# Task Contract

## Task ID

20260629-0017-92d-1-notification-and-phase-report-status-ux-repair

## Title

92D.1 — Notification and Phase Report Status UX Repair

## Status

active

## Mode

implementation

## Goal

Fix pcae notify status (stale/misleading after 92C/92D) and pcae phase-report show --latest (too sparse, should show detailed final-report-style view).

## Allowed Files

- src/pcae/commands/notifications.py
- src/pcae/commands/phase_reports.py
- src/pcae/commands/phase.py
- src/pcae/core/phase_reports.py
- tests/test_notifications_cli.py
- tests/test_phase_reports_cli.py
- docs/PHASE_92_NOTIFICATION_AND_PHASE_REPORT_STATUS_UX_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md

## Allowed Zones

- commands
- core
- tests
- docs
- tasks

## Forbidden Zones

- hooks
- config
- session
- policy
- package
- scripts

## Acceptance Criteria

- notify status shows accurate 92B/92C/92D state
- phase-report show --latest is detailed
- No misleading zeroes

## Acceptance Checks

- python -m pytest tests/test_phase_reports.py tests/test_phase_reports_cli.py tests/test_notifications.py tests/test_notifications_cli.py tests/test_telegram_notifications.py -q -ra
- python -m pytest -m "fast_green" -n auto -ra --durations=100

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-29T00:17:01.427218+02:00
