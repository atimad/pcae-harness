# Task Contract

## Task ID

20260731-1727-phase-147m-authority-evaluation-integration-implementation

## Title

Phase 147M: Authority Evaluation Integration Implementation

## Status

active

## Mode

implementation

## Goal

Implement the Authority Evaluation Service integration per AESIC-001 v1.3: AES, Decision Template Resolution, minimal concrete Registry adapter, Stage 1/Stage 2 lifecycle, immutable AER with two-tier compound-key + canonical pointer persistence, recovery, closed error taxonomy, and narrow additive integration into Interactive Workflow / Readiness / Publication / CHGR. No architectural redesign, no contract amendment, no runtime-capability expansion.

## Allowed Files

- src/pcae/aesic/**
- src/pcae/interactive_workflow/publication_handoff/models.py
- src/pcae/interactive_workflow/publication_handoff/handoff.py
- src/pcae/interactive_workflow/application/session_service.py
- src/pcae/governance/publication/record.py
- tests/test_phase_147m_*.py
- docs/implementation/PHASE_147M_AUTHORITY_EVALUATION_INTEGRATION_IMPLEMENTATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/TODO.md
- .pcae/policy.toml
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/active/*.md
- tasks/done/*.md

## Forbidden Files

- TBD


## Allowed Zones

- aesic
- interactive_workflow
- governance
- tests
- docs
- tasks
- policy
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

- TBD

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-31T17:27:48.946107+02:00
