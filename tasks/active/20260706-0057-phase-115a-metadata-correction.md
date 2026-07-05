# Task Contract

## Task ID

20260706-0057-phase-115a-metadata-correction

## Title

Phase 115A: Metadata Correction

## Status

active

## Mode

implementation

## Goal

Correct Phase 115A phase-completion metadata to satisfy legacy finalization-gate trust-field expectations before governed push and post-push canonicalization. Bookkeeping only; no architecture changes, no runtime implementation, no lifecycle behavior changes.

## Allowed Files

- .pcae/phase-completion-metadata.json
- tasks/DONE.md
- tasks/active/**

## Forbidden Files

- src/pcae/core/repository_transition_validator.py
- src/pcae/core/notification_certification.py
- src/pcae/core/canonical_artifact_promotion.py
- src/pcae/core/notifications.py
- src/pcae/core/push_state_reconciliation.py
- src/pcae/core/post_push_canonicalization.py
- src/pcae/core/handoff_verification.py
- src/pcae/core/permission_broker.py
- src/pcae/commands/phase.py
- src/pcae/commands/task.py
- src/pcae/commands/push.py
- src/pcae/commands/agent.py


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

- Phase 115A metadata has required finalization-gate test result keys
- Phase 115A metadata governance push-check wording is clean
- Execution capability remains unavailable

## Acceptance Checks

- pcae health
- pcae check
- pcae doctor task-memory
- pcae push check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-06T00:57:52.291804+02:00
