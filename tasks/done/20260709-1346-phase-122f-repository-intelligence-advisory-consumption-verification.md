# Task Contract

## Task ID

20260709-1346-phase-122f-repository-intelligence-advisory-consumption-verification

## Title

Phase 122F Repository Intelligence Advisory Consumption Verification

## Status

done

## Mode

verification

## Goal

Independently verify the Phase 122E Repository Intelligence Advisory Context Builder prototype against the 122A architecture, 122B frozen contract, 122C verification conclusions, and 122D prototype plan; repair only genuine defects found during verification without expanding scope.

## Allowed Files

- docs/PHASE_122_REPOSITORY_INTELLIGENCE_ADVISORY_CONSUMPTION_VERIFICATION.md
- src/pcae/advisory/**
- tests/test_phase_122e_repository_intelligence_advisory_context.py
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/DECISIONS.md
- tasks/active

## Forbidden Files

- src/pcae/repository_intelligence/**
- schemas/**


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

- Verify architecture conformance (122A), contract conformance (122B), and prototype plan conformance (122D).
- Verify Repository Intelligence is consumed exclusively through the Track 121 Query Layer with no direct access.
- Verify the Advisory Context Package contains selections, attribution bundle, limitation bundle, boundary disclosure bundle, and metadata.
- Verify deterministic context generation across repeated executions.
- Verify attribution, limitation, and boundary disclosure preservation.
- Verify read-only guarantees and fail-closed behavior for all seven failure modes, including missing limitation.
- Run Advisory Context Builder tests, Query Layer regression tests, Repository Knowledge Snapshot regression tests, and fast_green.
- Repair only genuine defects found; document each correction; do not expand scope.
- Confirm no Advisory reasoning, Decision Evaluation integration, or execution capability was introduced; runtime remains Observed / observe / execution unavailable.
- Recommend 123A as the next phase.

## Acceptance Checks

- pcae health
- pcae check
- pcae doctor task-memory
- pcae runtime inspect
- pcae notify status

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-09T13:46:09.085211+02:00
