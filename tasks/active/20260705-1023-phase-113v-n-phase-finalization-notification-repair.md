# Task Contract

## Task ID

20260705-1023-phase-113v-n-phase-finalization-notification-repair

## Title

Phase 113V.N: Phase Finalization Notification Repair

## Status

active

## Mode

implementation

## Goal

Repair the phase-finalization notification asymmetry: fix pcae skill invoke phase-finalization target resolution and add notification-dispatch idempotency to pcae phase complete.

## Allowed Files

- src/pcae/core/agent.py
- src/pcae/core/phase_reports.py
- src/pcae/commands/agent.py
- src/pcae/commands/phase.py
- src/pcae/commands/task.py
- tests/test_phase_113v_n_notification_finalization_repair.py
- docs/PHASE_113V_NOTIFICATION_FINALIZATION_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/20260705-1023-phase-113v-n-phase-finalization-notification-repair.md
- .pcae/phase-completion-metadata.json

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

- pcae skill invoke phase-finalization no longer returns target_unresolved for valid completed trusted pushed phases
- pcae phase complete notification dispatch is idempotent (no duplicate Telegram send for same phase_id+commit)
- Missing PCAE_NOTIFY_ENABLED is reported accurately, never conflated with target_unresolved

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-05T10:23:59.078992+02:00
