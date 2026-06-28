# Task Contract

## Task ID

20260628-2356-92c-telegram-outbound-phase-report-delivery

## Title

92C — Telegram Outbound Phase Report Delivery

## Status

done

## Mode

implementation

## Goal

Implement Telegram as an outbound notification sink using the 92B pluggable notification foundation. Manual send-report command only. No inbound, no polling, no remote shell.

## Allowed Files

- src/pcae/core/notifications.py
- src/pcae/commands/notifications.py
- src/pcae/cli.py
- tests/test_telegram_notifications.py
- tests/test_notifications.py
- docs/PHASE_92_TELEGRAM_OUTBOUND_PHASE_REPORT_DELIVERY.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md

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

- TelegramSink implementing NotificationSink protocol
- sendMessage + sendDocument via urllib
- Env var config: PCAE_TELEGRAM_BOT_TOKEN, PCAE_TELEGRAM_CHAT_ID
- CLI: pcae notify send-report --latest
- Tests with mocked HTTP, no real network
- Fast-green passes

## Acceptance Checks

- python -m pytest tests/test_notifications.py tests/test_notifications_cli.py tests/test_telegram_notifications.py -q -ra
- python -m pytest -m "fast_green" -n auto -ra --durations=100

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-28T23:56:54.502867+02:00
