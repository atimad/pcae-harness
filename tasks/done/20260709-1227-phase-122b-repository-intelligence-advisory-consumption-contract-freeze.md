# Task Contract

## Task ID

20260709-1227-phase-122b-repository-intelligence-advisory-consumption-contract-freeze

## Title

Phase 122B Repository Intelligence Advisory Consumption Contract Freeze

## Status

done

## Mode

contract-freeze

## Goal

Freeze the canonical Repository Intelligence Advisory Consumption Contract governing how Advisory may consume Repository Intelligence via the Track 121 read-only Query Layer, binding for 122C-122F, without implementing any code, tests, or schema changes.

## Allowed Files

- docs/PHASE_122_REPOSITORY_INTELLIGENCE_ADVISORY_CONSUMPTION_CONTRACT_FREEZE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/DECISIONS.md
- tasks/active

## Forbidden Files

- src/**
- tests/**
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

- Define the immutable Advisory Consumption Contract binding for 122C, 122D, 122E, 122F.
- Define architectural relationships between Repository Knowledge Snapshot, Repository Intelligence Query Layer, Advisory Runtime, Advisory Context, Repository State, Evidence, Decision Evaluation, and Runtime.
- Define Advisory responsibilities: permitted operations and prohibited operations.
- Define the query contract restricting access to the Track 121 read-only Query Layer only.
- Define the context contract, attribution contract, limitation contract, and boundary disclosure contract.
- Define the determinism contract: no inference, no probabilistic behavior, no AI augmentation.
- Define the fail-closed failure contract for unsupported snapshot, unsupported schema version, corrupted Repository Intelligence, missing attribution, missing limitation, missing boundary disclosure, and invalid query result.
- Define the governance contract and compatibility with Track 119, Track 120, and Track 121.
- Define deferred capabilities and strict non-goals; carry forward known inherited issues without repair.
- Introduce no implementation, source code change, test code change, or schema change; preserve runtime posture as Observed / observe / execution unavailable.
- Recommend 122C as the next phase.

## Acceptance Checks

- pcae health
- pcae check
- pcae doctor task-memory
- pcae runtime inspect
- pcae notify status

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-09T12:27:50.323644+02:00
