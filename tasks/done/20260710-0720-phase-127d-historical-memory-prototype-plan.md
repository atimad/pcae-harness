# Task Contract

## Task ID

20260710-0720-phase-127d-historical-memory-prototype-plan

## Title

Phase 127D Historical Memory Prototype Plan

## Status

done

## Mode

architecture

## Goal

Produce the definitive implementation plan for the first deterministic, read-only Historical Memory Builder, bounded by the 127B contract and independently verified in 127C. Resolve 127C's two carried-forward findings (historical_reference/reference_type explicit naming, null-boundary time reference ordering). Ground the plan in real, currently-available repository data sources (task contracts, git log, RKS envelope) rather than reasoning abstractly. Documentation only -- no generator, no source code, no test code, no schema change, no runtime behavior change.

## Allowed Files

- docs/PHASE_127_HISTORICAL_MEMORY_PROTOTYPE_PLAN.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/20260710-0720-phase-127d-historical-memory-prototype-plan.md

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

- Plan grounded in real repository data sources (task contracts, git log, RKS envelope), not abstract reasoning -- mirrors 126D's grounding discipline
- Resolves 127C Finding 1 (historical_reference/reference_type) and Finding 2 (null-boundary ordering) explicitly
- Defines 10-stage pipeline, identifier algorithm, node/relationship mapping tables, determinism/evidence/failure/versioning strategy per 127B contract
- Defines verification strategy for 127F and objective acceptance criteria for 127E
- No schema, source code, test code, generator, or storage introduced
- Runtime remains Observed/observe/execution-unavailable; no implementation occurred

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-10T07:20:41.185934+02:00
