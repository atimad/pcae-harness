# Task Contract

## Task ID

20260709-2246-phase-126e-dependency-knowledge-graph-prototype

## Title

Phase 126E Dependency Knowledge Graph Prototype

## Status

done

## Mode

implementation

## Goal

Implement the first deterministic, read-only Dependency Knowledge Graph Builder exactly as defined by Track 126 documentation (126A-126D). Consume Repository Intelligence exclusively through the Query Layer. No traversal, reasoning, or execution capability.

## Allowed Files

- src/pcae/repository_intelligence/dependency_graph/__init__.py
- src/pcae/repository_intelligence/dependency_graph/graph_builder.py
- src/pcae/repository_intelligence/dependency_graph/graph_validation.py
- src/pcae/repository_intelligence/dependency_graph/persistence.py
- src/pcae/repository_intelligence/dependency_graph/graph_generator.py
- src/pcae/commands/repository_intelligence.py
- src/pcae/cli.py
- tests/test_phase_126e_dependency_knowledge_graph_prototype.py
- docs/PHASE_126_DEPENDENCY_KNOWLEDGE_GRAPH_PROTOTYPE_IMPLEMENTATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/20260709-2246-phase-126e-dependency-knowledge-graph-prototype.md

## Forbidden Files

- TBD


## Allowed Zones

- commands
- cli
- tests
- docs
- tasks
- unclassified

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

- Deterministic graph generation from Repository Knowledge Snapshot via Query Layer only
- Fail-closed on invalid/unsupported input, missing provenance/limitations/boundary
- No graph traversal, reasoning, or execution capability introduced
- Regression suites for Tracks 120-124 and fast_green pass

## Acceptance Checks

- python -m pytest tests/test_phase_120e_repository_knowledge_snapshot.py tests/test_phase_121e_repository_intelligence_query.py tests/test_phase_122e_repository_intelligence_advisory_context.py tests/test_phase_123e_repository_intelligence_change_impact.py tests/test_phase_124e_repository_intelligence_hardening.py tests/test_phase_126e_dependency_knowledge_graph_prototype.py -q

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-09T22:46:04.279414+02:00
