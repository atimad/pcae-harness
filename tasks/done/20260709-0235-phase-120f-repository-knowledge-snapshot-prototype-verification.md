# Task Contract

## Task ID

20260709-0235-phase-120f-repository-knowledge-snapshot-prototype-verification

## Title

Phase 120F Repository Knowledge Snapshot Prototype Verification

## Status

done

## Mode

verification

## Goal

Independently verify the Phase 120E Repository Knowledge Snapshot prototype against the Phase 119 schemas and Phase 120A-120D architecture, contract, verification conclusions, and implementation plan without adding new functionality.

## Allowed Files

- docs/PHASE_120_REPOSITORY_KNOWLEDGE_SNAPSHOT_PROTOTYPE_VERIFICATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/DECISIONS.md
- tasks/active
- tasks/active/20260709-0235-phase-120f-repository-knowledge-snapshot-prototype-verification.md

## Forbidden Files

- src/pcae/repository_intelligence/source_inventory.py
- src/pcae/repository_intelligence/attribution.py
- src/pcae/repository_intelligence/snapshot_builder.py
- src/pcae/repository_intelligence/persistence.py
- src/pcae/repository_intelligence/snapshot_generator.py
- schemas/repository_intelligence/artifacts/repository_knowledge_snapshot.schema.json


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

- Architecture, contract, schema, determinism, attribution, limitation, unknown-handling, persistence, read-only, failure, governance, and regression verification documented.
- No new Repository Intelligence functionality, execution capability, query layer, graph traversal, runtime plugin, AI provider integration, or network dependency introduced.

## Acceptance Checks

- python -m pytest tests/test_phase_120e_repository_knowledge_snapshot.py -q
- python -m pytest -m "fast_green" -n auto -ra --durations=50
- pcae health
- pcae check
- pcae doctor task-memory
- pcae runtime inspect
- /bin/zsh -lc 'source ~/.config/pcae/telegram.env && pcae notify status'

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-09T02:35:57.292761+02:00
