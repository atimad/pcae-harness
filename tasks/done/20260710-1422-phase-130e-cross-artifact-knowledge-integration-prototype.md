# Task Contract

## Task ID

20260710-1422-phase-130e-cross-artifact-knowledge-integration-prototype

## Title

Phase 130E Cross-Artifact Knowledge Integration Prototype

## Status

done

## Mode

implementation

## Goal

Implement the first deterministic, read-only Cross-Artifact Knowledge Integration prototype exactly as scoped by 130A-130D: a new cross_artifact_integration package that connects existing Change Impact impacted entities to existing Dependency Knowledge Graph nodes via already-existing stable identifiers, reusing the existing dependency_context_reference schema shape, with full provenance/uncertainty/limitation/boundary preservation. No reasoning, inference, Decision Evaluation, Execution Planning, execution capability, or runtime plugins.

## Allowed Files

- src/pcae/repository_intelligence/cross_artifact_integration/__init__.py
- src/pcae/repository_intelligence/cross_artifact_integration/integration_builder.py
- src/pcae/repository_intelligence/cross_artifact_integration/integration_validation.py
- src/pcae/repository_intelligence/cross_artifact_integration/persistence.py
- src/pcae/repository_intelligence/cross_artifact_integration/integration_generator.py
- src/pcae/cli.py
- src/pcae/commands/repository_intelligence.py
- tests/test_phase_130e_cross_artifact_knowledge_integration_prototype.py
- docs/PHASE_130_CROSS_ARTIFACT_KNOWLEDGE_INTEGRATION_PROTOTYPE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/20260710-1422-phase-130e-cross-artifact-knowledge-integration-prototype.md

## Forbidden Files

- TBD


## Allowed Zones

- commands
- tests
- docs
- tasks
- cli
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

- Implements a new cross_artifact_integration package producing a deterministic, entirely derivative integrated knowledge package that populates dependency_context_reference-shaped records connecting Change Impact impacted entities to Dependency Knowledge Graph nodes via existing stable identifiers only
- Preserves authority, provenance (six elements), identity (no fuzzy/merged/replacement identifiers), uncertainty, limitations, and boundary disclosures unchanged from source artifacts
- Demonstrates deterministic output, read-only guarantees, and fail-closed behavior for missing/invalid/incompatible source artifacts
- Reuses serialize_deterministic_json and existing identifier-derivation logic; introduces no parallel serialization or identifier logic
- Adds regression test coverage; all regression suites (RKS, Query Layer, Advisory, Change Impact, DKG, Historical Memory), compileall, and fast_green pass
- No reasoning, inference, Decision Evaluation, Execution Planning, execution capability, runtime plugins, or schema changes; runtime remains Observed/observe/execution-unavailable; PFN-001 satisfied

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-10T14:22:52.933387+02:00
