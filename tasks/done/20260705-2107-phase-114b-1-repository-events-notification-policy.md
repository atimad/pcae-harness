# Task Contract

## Task ID

20260705-2107-phase-114b-1-repository-events-notification-policy

## Title

Phase 114B.1: Repository Events & Notification Policy

## Status

done

## Mode

implementation

## Goal

Formalize Repository Events as a first-class Repository State Kernel primitive alongside Repository State, Repository Transition, and Repository Artifact; freeze the Repository Event taxonomy and Notification Policy that emerged from the 114B forensic verification. Architecture/documentation only -- no runtime, dispatch, validator, or promotion behavior changes.

## Allowed Files

- docs/PCAE_REPOSITORY_EVENTS.md
- docs/PCAE_NOTIFICATION_POLICY.md
- docs/PHASE_114B1_REPOSITORY_EVENTS_NOTIFICATION_POLICY.md
- tests/test_phase_114b1_repository_events_notification_policy.py
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- .pcae/phase-completion-metadata.json
- tasks/active/**

## Forbidden Files

- src/pcae/core/repository_transition_validator.py
- src/pcae/core/repository_transition_integration.py
- src/pcae/core/notification_certification.py
- src/pcae/core/canonical_artifact_promotion.py
- src/pcae/core/notifications.py
- src/pcae/commands/notifications.py
- src/pcae/commands/phase.py
- src/pcae/commands/task.py
- src/pcae/core/phase_reports.py
- src/pcae/commands/push.py
- src/pcae/core/permission_broker.py


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

- Repository State Kernel four-primitives model frozen
- Repository Events become a first-class architectural concept
- Notification Policy becomes explicitly defined
- Quarantined/rejected/human-review transitions defined as observable events
- Wire diagram updated
- No implementation added
- Execution capability remains unavailable

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-05T21:07:32.537736+02:00
