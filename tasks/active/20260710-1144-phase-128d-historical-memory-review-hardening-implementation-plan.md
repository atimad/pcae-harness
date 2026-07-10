# Task Contract

## Task ID

20260710-1144-phase-128d-historical-memory-review-hardening-implementation-plan

## Title

Phase 128D Historical Memory Review Hardening Implementation Plan

## Status

active

## Mode

planning

## Goal

Produce the definitive bounded implementation plan for 128E Historical Memory hardening, explicitly resolving both 128C findings (temporal-ordering wording precision; historical_generator.py scope naming) via terminology/documentation refinement only. Documentation only -- no implementation, no schema changes, no source or test code changes.

## Allowed Files

- docs/PHASE_128_HISTORICAL_MEMORY_REVIEW_HARDENING_IMPLEMENTATION_PLAN.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/20260710-1144-phase-128d-historical-memory-review-hardening-implementation-plan.md

## Forbidden Files

- TBD


## Allowed Zones

- docs
- tasks

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

- Defines a bounded implementation plan for 128E covering implementation/terminology/persistence/serialization/documentation/governance/interface consistency and deterministic-behavior preservation, with no functional expansion
- Explicitly resolves 128C Finding 1 (temporal vs persisted-artifact ordering wording) and Finding 2 (historical_generator.py scope naming) via documentation/terminology refinement only, preserving existing behavior
- Defines the 10-step implementation pipeline and measurable 128E acceptance criteria (no functional change, determinism/evidence/attribution/temporal/read-only/serialization/CLI/governance compatibility preserved)
- Defines regression strategy against Historical Memory, Dependency Knowledge Graph, Change Impact, Advisory Context, Query Layer, and Repository Knowledge Snapshot, and 128F verification strategy
- Carries forward only the two known technical-debt items (persistence naming, historical_generator scope) and all deferred capabilities, without repairing or implementing any of them
- No implementation, schema, source code, test code, or runtime behavior change; runtime remains Observed/observe/execution-unavailable

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-10T11:44:50.620828+02:00
