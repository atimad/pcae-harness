# Task Contract

## Task ID

20260706-0243-phase-115b-repository-evidence-framework-contract-freeze

## Title

Phase 115B: Repository Evidence Framework Contract Freeze

## Status

active

## Mode

implementation

## Goal

Freeze the Repository Evidence Framework contract introduced in 115A: exact Evidence fields, identity, categories, determinism levels, confidence semantics, freshness semantics, provider contract, conflict semantics, explanation references, persistence boundary, and SLM/AI evidence boundary. Architecture and contract only; no runtime behavior, no Repository Transition Validator behavior changes, no lifecycle command changes, no Notification Policy changes, no Repository Skills implementation, no execution, authorization, Permission Broker enforcement, plugins, Telegram inbound, REST, Web UI, or Dashboard.

## Allowed Files

- docs/PCAE_REPOSITORY_EVIDENCE_FRAMEWORK.md
- docs/PCAE_EVIDENCE_PROVIDER_CONTRACT.md
- docs/PHASE_115B_REPOSITORY_EVIDENCE_CONTRACT_FREEZE.md
- tests/test_phase_115b_repository_evidence_contract_freeze.py
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/DECISIONS.md
- tasks/TODO.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
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

- docs
- tests
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

- Evidence contract frozen
- Evidence Provider contract frozen
- Determinism, confidence, and freshness semantics frozen
- Explanation-by-evidence-reference defined
- SLM/AI evidence boundary defined
- No implementation added
- Execution capability remains unavailable

## Acceptance Checks

- python -m pytest tests/test_phase_115b_repository_evidence_contract_freeze.py
- pcae health
- pcae check
- pcae doctor task-memory
- pcae push check
- pcae session bootstrap --compact --profile implementation
- pcae runtime inspect --json
- pcae notify status

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Phase Notes

- Architecture/contract only.
- Evidence informs decisions; it does not decide.
- Evidence remains evaluation-scoped and does not become a kernel primitive.
- No runtime implementation, lifecycle command change, validator behavior change,
  Notification Policy change, Repository Skill implementation, execution,
  authorization, Permission Broker enforcement, plugin, Telegram inbound, REST,
  Web UI, Dashboard, tag, release, or package publication is in scope.

## Created Timestamp

2026-07-06T02:43:29.923588+02:00
