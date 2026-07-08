# Task Contract

## Task ID

20260708-1948-phase-119p-repository-knowledge-snapshot-schema-verification

## Title

Phase 119P Repository Knowledge Snapshot schema verification

## Status

active

## Mode

implementation

## Goal

Verify the Repository Knowledge Snapshot JSON Schema for JSON validity, Draft 2020-12 consistency, reference consistency, shared component reuse, source attribution, uncertainty preservation, boundary preservation, documentation clarity, and no-go scope without adding schemas, validators, CLI, tests, models, extraction, scanning, graph, impact, Advisory, runtime, execution, enforcement, or lifecycle behavior.

## Allowed Files

- docs/PHASE_119_REPOSITORY_INTELLIGENCE_EXECUTABLE_SCHEMA_REPOSITORY_KNOWLEDGE_SNAPSHOT_VERIFICATION.md
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

- Repository Knowledge Snapshot schema verification document exists and concludes readiness or repair status.
- All Repository Intelligence schema files parse as valid JSON and declare Draft 2020-12.
- Repository Knowledge Snapshot refs resolve locally and expected shared component reuse is verified.
- No new artifact-family schema, validator, CLI, test, model, extraction, scanning, graph, impact, Advisory, runtime, execution, enforcement, source, or test changes are added.

## Acceptance Checks

- pcae health
- pcae check
- pcae doctor task-memory
- pcae push check
- pcae runtime inspect

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-08T19:48:40.015105+02:00
