# Task Contract

## Task ID

20260905-0047-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-30r-5r-2-1r-1r-2r-1r-1r-1r-1-1r-1r-durable-telegram-notification-acceptance-receipts-phase-completion-notification-auditability-repair

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R: Durable Telegram Notification Acceptance Receipts + Phase-Completion Notification Auditability Repair

## Status

active

## Mode

implementation

## Goal

Repair the notification-lifecycle observability defect: real Telegram API responses (ok, message_id) are collapsed into an in-memory boolean and discarded, leaving no durable post-hoc audit trail. Implement minimal durable acceptance-receipt persistence for TelegramSink summary+document operations, bound to phase/report/sink/operation, excluding secrets, with explicit PREPARED/API_ACCEPTED/API_REJECTED/TRANSPORT_FAILED/OUTCOME_UNCERTAIN state machine. .last-notified.json remains dedup-only. No re-dispatch of the affected historical IV. No F-5/runtime/contract/dependency change unless separately adjudicated (BLOCK if required).

## Allowed Files

- src/pcae/core/notifications.py
- src/pcae/core/phase_reports.py
- tests/**
- docs/**
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/**
- .pcae/**

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

- Durable acceptance receipt persisted for summary and document Telegram operations independently, with message_id when returned
- No secrets (bot token, auth headers) persisted
- No historical report rewritten; affected IV report unchanged
- No re-dispatch performed in this phase
- No F-5/runtime/contract/dependency change

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-05T00:47:35.699455+02:00
