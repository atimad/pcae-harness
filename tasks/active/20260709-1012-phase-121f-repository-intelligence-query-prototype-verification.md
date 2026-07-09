# Task Contract

## Task ID

20260709-1012-phase-121f-repository-intelligence-query-prototype-verification

## Title

Phase 121F Repository Intelligence Query Prototype Verification

## Status

active

## Mode

verification

## Goal

Independently verify the Phase 121E Repository Intelligence Query prototype against the 121A architecture, 121B frozen contract, 121C verification conclusions, and 121D prototype plan, while preserving observe-only runtime and no execution capability.

## Allowed Files

- src/pcae/repository_intelligence/**
- src/pcae/commands/**
- src/pcae/cli.py
- tests/**
- docs/PHASE_121_REPOSITORY_INTELLIGENCE_QUERY_PROTOTYPE_VERIFICATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/DECISIONS.md
- tasks/active

## Forbidden Files

- schemas/**
- .pcae/repository-intelligence/**


## Allowed Zones

- TBD

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

- Verify the 121E query prototype conforms to 121A architecture, 121B frozen contract, 121C verification conclusions, and 121D plan.
- Verify schema compatibility for 119O.1.0-json-schema and fail-closed behavior for unsupported versions.
- Verify supported query categories: entity, capability, architectural contract, attribution, limitation, boundary lookup.
- Verify deterministic repeated query results, attribution preservation, limitation and boundary propagation.
- Verify read-only behavior and fail-closed handling for missing/corrupted snapshot, unsupported schema, invalid/unsupported request, unknown entity.
- Run focused query tests, Repository Knowledge Snapshot regression tests, and fast-green.
- Preserve runtime posture as Observed / observe / execution unavailable; introduce no new functionality.
- Recommend 122A as the next phase.

## Acceptance Checks

- python -m pytest tests/test_phase_121e_repository_intelligence_query.py -q
- python -m pytest tests/test_phase_120e_repository_knowledge_snapshot.py -q
- pcae health
- pcae check
- pcae doctor task-memory
- pcae runtime inspect
- pcae notify status

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-09T10:12:04.439533+02:00
