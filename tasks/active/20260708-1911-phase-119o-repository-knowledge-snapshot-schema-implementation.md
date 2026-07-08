# Task Contract

## Task ID

20260708-1911-phase-119o-repository-knowledge-snapshot-schema-implementation

## Title

Phase 119O Repository Knowledge Snapshot schema implementation

## Status

active

## Mode

implementation

## Goal

Implement exactly one additional Repository Intelligence artifact-family JSON Schema, the Repository Knowledge Snapshot schema, as schema-only documentation/artifacts without extraction, repository scanning, validators, CLI, models, tests, graph, impact, Advisory, Evidence, Decision Evaluation, runtime, execution, enforcement, or lifecycle behavior changes.

## Allowed Files

- schemas/repository_intelligence/artifacts/repository_knowledge_snapshot.schema.json
- schemas/repository_intelligence/README.md
- docs/PHASE_119_REPOSITORY_INTELLIGENCE_EXECUTABLE_SCHEMA_REPOSITORY_KNOWLEDGE_SNAPSHOT.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- tasks/active
- tasks/done
- .pcae/session.json
- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json

## Forbidden Files

- src
- tests
- .github
- pyproject.toml
- schemas/repository_intelligence/artifacts/repository_intelligence_package.schema.json
- schemas/repository_intelligence/artifacts/historical_memory_snapshot.schema.json
- schemas/repository_intelligence/artifacts/dependency_knowledge_graph_snapshot.schema.json
- schemas/repository_intelligence/artifacts/change_impact_report.schema.json
- schemas/repository_intelligence/artifacts/advisory_intelligence_context_package.schema.json
- schemas/repository_intelligence/artifacts/query_result.schema.json


## Allowed Zones

- TBD

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

- Exactly one new artifact-family schema is implemented: Repository Knowledge Snapshot.
- The schema is Draft 2020-12, valid JSON, has unique id, references shared components where appropriate, and preserves boundaries.
- README and phase documentation describe structural validation scope, semantic exclusions, and non-goals.
- No validator, CLI, models, automated tests, extraction, scanning, graph, impact, Advisory, Evidence, Decision Evaluation, runtime, execution, enforcement, or lifecycle behavior is added.

## Acceptance Checks

- pcae health
- pcae check
- pcae doctor task-memory
- pcae push check
- pcae runtime inspect

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-08T19:11:46.441087+02:00
