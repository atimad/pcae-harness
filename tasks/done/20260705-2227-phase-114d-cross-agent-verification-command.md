# Task Contract

## Task ID

20260705-2227-phase-114d-cross-agent-verification-command

## Title

Phase 114D: Cross-Agent Verification Command

## Status

done

## Mode

implementation

## Goal

Implement a model-agnostic, read-only repository handoff verification command (pcae agent verify-handoff or pcae verify handoff) that answers 'safe to continue?' by checking git state, task state, phase/report state, 114C live push-state reconciliation, notification state, architecture status, and runtime invariants (execution unavailable). Read-only containment infrastructure: no file mutation, no commit, no push, no notify, no finalize.

## Allowed Files

- docs/PHASE_114_CROSS_AGENT_VERIFICATION_COMMAND.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- .pcae/phase-completion-metadata.json
- tasks/active/**
- src/pcae/core/handoff_verification.py
- src/pcae/commands/agent.py
- src/pcae/cli.py
- tests/test_handoff_verification.py

## Forbidden Files

- src/pcae/commands/push.py
- src/pcae/core/repository_transition_validator.py
- src/pcae/core/notification_certification.py
- src/pcae/core/canonical_artifact_promotion.py
- src/pcae/core/notifications.py
- src/pcae/core/permission_broker.py
- src/pcae/core/push_state_reconciliation.py


## Allowed Zones

- core
- commands
- cli
- tests
- docs
- tasks
- config

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

- Cross-agent verification command implemented
- Command is read-only
- Command detects unsafe handoff state
- JSON and human output available
- Live push-state reconciliation used
- Runtime execution-unavailable invariant checked
- No lifecycle mutation
- Execution capability remains unavailable

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-05T22:27:02.997972+02:00
