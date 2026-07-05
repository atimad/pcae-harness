# Task Contract

## Task ID

20260705-2341-phase-114e-model-containment-drill

## Title

Phase 114E: Model Containment Drill

## Status

done

## Mode

implementation

## Goal

Prove PCAE can contain DeepSeek-style model drift by deliberately reproducing 12 known failure scenarios (wrong phase identity, stale metadata, stale commit hashes, missing recommended_next_phase, bad test result structure, duplicate notification, silent notification prevention, push-state mismatch both directions, architecture overclaim, dirty working tree, latest report mismatch, execution availability violation) in isolated scratch repos and verifying invalid states are rejected, quarantined, or reported before becoming canonical. Verification-only phase: no new runtime mechanism, tests and documentation only.

## Allowed Files

- tests/test_model_containment_drill.py
- docs/PHASE_114_MODEL_CONTAINMENT_DRILL.md
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
- src/pcae/core/post_push_canonicalization.py
- src/pcae/core/handoff_verification.py
- src/pcae/commands/phase.py
- src/pcae/commands/task.py
- src/pcae/commands/push.py
- src/pcae/commands/agent.py
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

- DeepSeek-style drift scenarios are reproduced safely
- Invalid states are rejected, quarantined, or reported before canonical promotion
- latest.json/latest.md remain protected
- duplicate notification is prevented
- live push-state reconciliation verified
- verify-handoff catches unsafe handoff states
- post-push reconciliation updates canonical report
- Telegram final report delivered
- execution capability remains unavailable

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-05T23:41:14.358477+02:00
