# Task Contract

## Task ID

20260709-0547-phase-121a-repository-intelligence-query-layer-architecture

## Title

Phase 121A Repository Intelligence Query Layer Architecture

## Status

done

## Mode

architecture

## Goal

Design the Repository Intelligence Query Layer as a deterministic, read-only architecture for consuming existing Repository Intelligence artifacts without implementing query execution or changing runtime behavior.

## Allowed Files

- docs/PHASE_121_REPOSITORY_INTELLIGENCE_QUERY_LAYER_ARCHITECTURE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/DECISIONS.md
- tasks/active
- tasks/active/20260709-0547-phase-121a-repository-intelligence-query-layer-architecture.md

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

- Architecture document defines query layer purpose, relationships, scope, conceptual layers, query model, input/output models, query categories, determinism, attribution, boundary, failure, governance, extensibility, and Track 121 roadmap.
- No query engine, parser, CLI, API, models, validators, runtime plugin, repository scanning, generation, graph traversal, Advisory integration, execution planning, or execution capability implemented.

## Acceptance Checks

- pcae health
- pcae check
- pcae doctor task-memory
- pcae runtime inspect
- /bin/zsh -lc 'source ~/.config/pcae/telegram.env && pcae notify status'

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-09T05:47:53.565353+02:00
