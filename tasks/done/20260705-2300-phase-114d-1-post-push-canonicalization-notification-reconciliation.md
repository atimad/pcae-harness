# Task Contract

## Task ID

20260705-2300-phase-114d-1-post-push-canonicalization-notification-reconciliation

## Title

Phase 114D.1: Post-Push Canonicalization & Notification Reconciliation

## Status

done

## Mode

implementation

## Goal

Fix the live defect where pcae agent verify-handoff correctly reports FAIL because .pcae/phase-completion-metadata.json declares a phase (114D) that was never canonically promoted to .pcae/phase-reports/latest.json (still 114A), even though the repository is genuinely clean and pushed. After a governed pcae push succeeds (or confirms nothing to push while live state is clean), detect pending metadata-vs-canonical-report mismatch, and if live push state is clean, re-run finalization (reusing phase.py's existing _finalize_report_and_notify, which already incorporates 114C's live push-state reconciliation and 114B's notification certification/idempotency) to promote the canonical report and dispatch the eligible notification exactly once.

## Allowed Files

- src/pcae/core/post_push_canonicalization.py
- src/pcae/commands/push.py
- tests/test_post_push_canonicalization.py
- docs/PHASE_114D1_POST_PUSH_CANONICALIZATION_NOTIFICATION_RECONCILIATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- .pcae/phase-completion-metadata.json
- tasks/active/**

## Forbidden Files

- src/pcae/core/repository_transition_validator.py
- src/pcae/core/notification_certification.py
- src/pcae/core/canonical_artifact_promotion.py
- src/pcae/core/notifications.py
- src/pcae/core/push_state_reconciliation.py
- src/pcae/core/permission_broker.py
- src/pcae/commands/phase.py
- src/pcae/commands/task.py


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

- latest.json phase_id equals current completed phase
- pcae agent verify-handoff no longer fails due to stale latest report
- origin/main..HEAD = 0
- exactly one Telegram final notification is sent when configured/enabled
- repeated reconciliation does not duplicate notification
- execution capability remains unavailable

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-05T23:00:32.353973+02:00
