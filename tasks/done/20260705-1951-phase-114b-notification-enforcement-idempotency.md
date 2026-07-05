# Task Contract

## Task ID

20260705-1951-phase-114b-notification-enforcement-idempotency

## Title

Phase 114B: Notification Enforcement & Idempotency

## Status

done

## Mode

implementation

## Goal

Integrate notification dispatch into the Repository State Kernel so external notifications become certified consequences of canonical repository state; wire the already-frozen Repository Transition Validator NOTIFY transition kind and notification_eligible() into the real dispatch call sites in pcae phase complete and pcae task finish --commit, replacing the two independent ad hoc idempotency/suppression checks with one shared certification function.

## Allowed Files

- src/pcae/core/notification_certification.py
- src/pcae/core/repository_transition_integration.py
- src/pcae/core/repository_transition_validator.py
- src/pcae/commands/phase.py
- src/pcae/commands/task.py
- src/pcae/commands/notifications.py
- src/pcae/core/notifications.py
- src/pcae/core/phase_reports.py
- tests/test_notification_certification_idempotency.py
- docs/PCAE_NOTIFICATION_CERTIFICATION.md
- docs/PHASE_114_NOTIFICATION_ENFORCEMENT.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- tasks/active/**
- .pcae/phase-completion-metadata.json

## Forbidden Files

- src/pcae/commands/push.py
- src/pcae/core/runtime_snapshot.py
- src/pcae/core/permission_broker.py
- src/pcae/core/advisory_runtime.py


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

- Notifications dispatched only from certified canonical artifacts
- Exactly one notification per certified transition
- Duplicate notifications impossible
- Notification failures never corrupt repository state
- Notification retries are deterministic
- Execution capability remains unavailable

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-05T19:51:24.483694+02:00
