# Task Contract

## Task ID

20260629-0003-92d-automatic-phase-finalization-notification-hook

## Title

92D — Automatic Phase-Finalization Notification Hook

## Status

active

## Mode

implementation

## Goal

Integrate 92A/92B/92C into phase-finalization: auto-create phase reports and optionally dispatch notifications on pcae phase complete. Notification failure is non-fatal.

## Allowed Files

- src/pcae/commands/phase.py
- src/pcae/core/phase_reports.py
- tests/test_phase_reports.py
- docs/PHASE_92_AUTOMATIC_PHASE_FINALIZATION_NOTIFICATION_HOOK.md
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
- cli

## Enforcement Mode

advisory

## Acceptance Criteria

- Phase report auto-created on pcae phase complete
- Notification dispatch opt-in via PCAE_NOTIFY_ENABLED
- Telegram via existing env vars only
- Notification failure is non-fatal

## Acceptance Checks

- python -m pytest tests/test_phase_reports.py tests/test_phase_reports_cli.py tests/test_notifications.py tests/test_notifications_cli.py tests/test_telegram_notifications.py -q -ra
- python -m pytest -m "fast_green" -n auto -ra --durations=100

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-29T00:03:59.564540+02:00
