# Task Contract

## Task ID

20260826-1119-phase-149o-20l-7o-3m-rollback-readiness-evidence-automatic-consumption-architecture-and-integration

## Title

Phase 149O.20L.7O.3M: Rollback Readiness / Evidence Automatic Consumption Architecture and Integration

## Status

active

## Mode

implementation

## Goal

Reconstruct current rollback architecture from actual source; determine whether existing contracts support automating safe preparation/evidence consumption into the highest-level rollback entry point without inventing new readiness authority; implement only if safe, else stop and recommend a narrow contract phase.

## Allowed Files

- docs/PHASE_149O_20L_7O_3M_ROLLBACK_READINESS_EVIDENCE_AUTOMATIC_CONSUMPTION_ARCHITECTURE_AND_INTEGRATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- .pcae/fast-green-attribution/*
- tasks/DONE.md
- tasks/active/*
- tasks/done/*
- src/pcae/core/agent.py
- src/pcae/core/mutation_permission.py
- src/pcae/core/rollback_approval_evidence.py
- src/pcae/core/hatp_rollback_consumption.py
- src/pcae/core/enforcement_rollback.py
- src/pcae/core/permission_broker.py
- src/pcae/core/scope_preflight.py
- src/pcae/cli.py
- src/pcae/commands/agent.py
- src/pcae/commands/permission_broker.py
- tests/test_phase_149o_20l_7o_3m_rollback_readiness_evidence_automatic_consumption.py

## Forbidden Files

- TBD


## Allowed Zones

- TBD

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

strict

## Forbidden Changes

- TBD

## Acceptance Criteria

- Rollback architecture reconstructed from current source, not inherited summaries
- No new authoritative readiness contract invented without a dedicated contract phase
- Permission Broker remains authoritative and unbypassed
- Runtime remains Observed/observe/unavailable

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- fast_green attribution 0 attributable regressions

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-26T11:19:54.702027+02:00
