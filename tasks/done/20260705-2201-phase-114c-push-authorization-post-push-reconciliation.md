# Task Contract

## Task ID

20260705-2201-phase-114c-push-authorization-post-push-reconciliation

## Title

Phase 114C: Push Authorization & Post-Push Reconciliation

## Status

done

## Mode

implementation

## Goal

Fix the live 114B/114B.1 forensic finding: pcae phase complete/pcae task finish --commit read pushed_status/origin_main_head_count from stale, declared .pcae/phase-completion-metadata.json instead of live git state, causing a genuinely pushed repository to be incorrectly quarantined. Make live git state authoritative for current push state whenever determinable, reconcile against declared metadata, surface discrepancies as diagnostics, and route the reconciled state into notification eligibility.

## Allowed Files

- src/pcae/core/push_state_reconciliation.py
- src/pcae/commands/phase.py
- src/pcae/commands/task.py
- tests/test_push_state_reconciliation.py
- docs/PHASE_114_PUSH_AUTHORIZATION_POST_PUSH_RECONCILIATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- .pcae/phase-completion-metadata.json
- tasks/active/**

## Forbidden Files

- src/pcae/commands/push.py
- src/pcae/core/repository_transition_validator.py
- src/pcae/core/notification_certification.py
- src/pcae/core/canonical_artifact_promotion.py
- src/pcae/core/notifications.py
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

- Live push state is authoritative during finalization
- Stale push metadata cannot incorrectly quarantine a pushed repo
- Live unpushed state still blocks when appropriate
- Discrepancies are visible
- Notification eligibility uses reconciled push state
- Execution capability remains unavailable

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-05T22:01:58.874065+02:00
