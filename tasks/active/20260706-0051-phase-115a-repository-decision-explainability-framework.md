# Task Contract

## Task ID

20260706-0051-phase-115a-repository-decision-explainability-framework

## Title

Phase 115A: Repository Decision & Explainability Framework

## Status

active

## Mode

implementation

## Goal

Design and freeze the architecture and contracts by which PCAE explains every repository decision: evidence concepts, evidence providers, deterministic decision evaluation, explanations, repository skills, decision composition, canonical wire diagram, and future model-independent applicability. Architecture and contract only; no runtime implementation, no execution capability, no Repository Transition Validator changes, no Notification Policy changes, no lifecycle command changes, no Permission Broker changes, no plugins, no Telegram inbound, no REST, no Web UI, no Dashboard.

## Allowed Files

- docs/PCAE_DECISION_FRAMEWORK.md
- docs/PCAE_REPOSITORY_SKILLS.md
- docs/PHASE_115A_DECISION_EXPLAINABILITY_FRAMEWORK.md
- tests/test_phase_115a_decision_explainability_framework.py
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

- Runtime implementation
- Execution capability
- Repository Transition Validator changes
- Notification Policy changes
- Lifecycle command changes
- Permission Broker changes
- Plugin implementation
- Telegram inbound
- REST
- Web UI
- Dashboard

## Acceptance Criteria

- Repository Decision Framework frozen
- Evidence architecture defined
- Repository Skill architecture defined
- Explainability framework defined
- Canonical Mermaid wire diagram present
- Decision pipeline documented
- No runtime implementation
- Execution capability remains unavailable

## Acceptance Checks

- python -m pytest tests/test_phase_115a_decision_explainability_framework.py
- pcae health
- pcae check
- pcae doctor task-memory
- pcae push check
- pcae agent verify-handoff
- pcae session bootstrap --compact --profile implementation
- pcae runtime inspect --json
- pcae notify status

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-06T00:51:12.181204+02:00
