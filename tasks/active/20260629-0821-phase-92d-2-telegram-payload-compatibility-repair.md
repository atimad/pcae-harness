# Task Contract

## Task ID

20260629-0821-phase-92d-2-telegram-payload-compatibility-repair

## Title

Phase 92D.2 — Telegram Payload Compatibility Repair

## Status

active

## Mode

corrective

## Goal

Fix PCAE Telegram outbound delivery: repair sendMessage payload encoding (remove unsupported parse_mode, use URL-encoded form data), improve error-body reporting, and add tests.

## Allowed Files

- src/pcae/core/notifications.py
- tests/test_telegram_notifications.py
- docs/PHASE_92_TELEGRAM_PAYLOAD_COMPATIBILITY_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md

## Forbidden Files

- TBD


## Allowed Zones

- core
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

advisory

## Forbidden Changes

- TBD

## Acceptance Criteria

- TBD

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-29T08:21:00.406104+02:00
