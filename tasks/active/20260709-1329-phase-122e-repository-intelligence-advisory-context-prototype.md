# Task Contract

## Task ID

20260709-1329-phase-122e-repository-intelligence-advisory-context-prototype

## Title

Phase 122E Repository Intelligence Advisory Context Prototype

## Status

active

## Mode

implementation

## Goal

Implement the first deterministic, read-only Advisory Context Builder that consumes Repository Intelligence exclusively through the Track 121 Query Layer and assembles Repository Intelligence Advisory Context Packages, within the boundaries frozen by 122B, verified by 122C, and planned by 122D.

## Allowed Files

- src/pcae/advisory/**
- src/pcae/cli.py
- src/pcae/commands/advisory_context.py
- tests/test_phase_122e_repository_intelligence_advisory_context.py
- docs/PHASE_122_REPOSITORY_INTELLIGENCE_ADVISORY_CONTEXT_PROTOTYPE_IMPLEMENTATION.md
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

- Implement Advisory Context Builder consuming Repository Intelligence exclusively through the Track 121 Query Layer (execute_query); no direct Repository Intelligence artifact access.
- Implement deterministic context assembly, attribution preservation, limitation propagation, and boundary disclosure propagation.
- Implement Advisory context serialization and a minimal CLI command (pcae advisory context build).
- Implement fail-closed handling for invalid context request, invalid Query Layer result, missing attribution, missing limitation, missing boundary disclosure, unsupported Repository Intelligence version, and corrupted Repository Intelligence response.
- Implement focused verification tests: deterministic assembly, Query Layer integration, attribution/limitation/boundary preservation, serialization, fail-closed behavior, repeated deterministic execution, read-only guarantees.
- Document the implementation in docs/PHASE_122_REPOSITORY_INTELLIGENCE_ADVISORY_CONTEXT_PROTOTYPE_IMPLEMENTATION.md.
- Introduce no Advisory reasoning, no recommendations, no Decision Evaluation integration, no Repository Intelligence generation, no repository scanning, no execution capability, no runtime plugins, no AI or network access.
- Preserve runtime posture as Observed / observe / execution unavailable.
- Recommend 122F as the next phase.

## Acceptance Checks

- pcae health
- pcae check
- pcae doctor task-memory
- pcae runtime inspect
- pcae notify status

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-09T13:29:22.072826+02:00
