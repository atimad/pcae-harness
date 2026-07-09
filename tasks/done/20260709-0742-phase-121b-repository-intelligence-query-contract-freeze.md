# Task Contract

## Task ID

20260709-0742-phase-121b-repository-intelligence-query-contract-freeze

## Title

Phase 121B Repository Intelligence Query Contract Freeze

## Status

done

## Mode

documentation

## Goal

Freeze the canonical Repository Intelligence Query Contract for deterministic, read-only access to existing Repository Intelligence artifacts before any Track 121 planning or implementation.

## Allowed Files

- docs/PHASE_121_REPOSITORY_INTELLIGENCE_QUERY_CONTRACT_FREEZE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/DECISIONS.md
- tasks/active
- tasks/active/20260709-0742-phase-121b-repository-intelligence-query-contract-freeze.md

## Forbidden Files

- src/pcae/repository_intelligence/source_inventory.py
- src/pcae/repository_intelligence/attribution.py
- src/pcae/repository_intelligence/snapshot_builder.py
- src/pcae/repository_intelligence/persistence.py
- src/pcae/repository_intelligence/snapshot_generator.py
- schemas/repository_intelligence/artifacts/query_result.schema.json
- tests/test_phase_120e_repository_knowledge_snapshot.py


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

- Query contract freeze document defines purpose, scope, supported artifact source, query request model, result model, supported categories, determinism, attribution, boundary, failure, governance, versioning, future extensibility, and phase roadmap.
- No query engine, parser, language, CLI, REST, API, Python model, validator, runtime plugin, repository scanning, generation, graph traversal, Advisory integration, execution planning, or execution capability implemented.

## Acceptance Checks

- pcae health
- pcae check
- pcae doctor task-memory
- pcae runtime inspect
- /bin/zsh -lc 'source ~/.config/pcae/telegram.env && pcae notify status'

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-09T07:42:07.189201+02:00
