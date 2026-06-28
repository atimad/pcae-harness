# Task Contract

## Task ID

20260628-2351-92b-pluggable-notification-foundation

## Title

92B — Pluggable Notification Foundation

## Status

done

## Mode

implementation

## Goal

Implement a generic, pluggable notification foundation with event/sink/dispatcher model. No Telegram, no external network calls.

## Allowed Files

- src/pcae/core/notifications.py
- src/pcae/commands/notifications.py
- src/pcae/cli.py
- tests/test_notifications.py
- tests/test_notifications_cli.py
- docs/PHASE_92_PLUGGABLE_NOTIFICATION_FOUNDATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md

## Forbidden Files

- .githooks/**
- docs/LINKEDIN_ARTICLE_DRAFT.md
- docs/REAL_CAPTURED_TASKS.md

## Allowed Zones

- core
- commands
- cli
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

## Enforcement Mode

advisory

## Acceptance Criteria

- NotificationEvent/NotificationResult dataclasses, 4 sinks, dispatcher, tests

## Acceptance Checks

- python -m pytest tests/test_notifications.py tests/test_notifications_cli.py -q -ra
- python -m pytest -m "fast_green" -n auto -ra --durations=100

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-28T23:51:18.754952+02:00
