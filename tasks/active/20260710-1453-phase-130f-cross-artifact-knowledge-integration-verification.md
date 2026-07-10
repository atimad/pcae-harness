# Task Contract

## Task ID

20260710-1453-phase-130f-cross-artifact-knowledge-integration-verification

## Title

Phase 130F Cross-Artifact Knowledge Integration Verification

## Status

active

## Mode

verification

## Goal

Independently verify the completed 130E Cross-Artifact Knowledge Integration prototype by regenerating fresh artifacts and re-deriving every architectural invariant directly from source -- not trusting 130E's implementation, tests, generated artifacts, report, or prior verification. Repair only genuine implementation defects if discovered; document every repair.

## Allowed Files

- docs/PHASE_130_CROSS_ARTIFACT_KNOWLEDGE_INTEGRATION_VERIFICATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- src/pcae/repository_intelligence/cross_artifact_integration/integration_builder.py
- src/pcae/repository_intelligence/cross_artifact_integration/integration_validation.py
- src/pcae/repository_intelligence/cross_artifact_integration/persistence.py
- src/pcae/repository_intelligence/cross_artifact_integration/integration_generator.py
- tests/test_phase_130e_cross_artifact_knowledge_integration_prototype.py
- tasks/active/20260710-1453-phase-130f-cross-artifact-knowledge-integration-verification.md

## Forbidden Files

- TBD


## Allowed Zones

- docs
- tasks
- tests
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

- Independently regenerates fresh RKS, DKG, Historical Memory, and Cross-Artifact Integration artifacts from current repository state, never reusing existing generated artifacts
- Performs independent schema validation, cross-artifact integrity, authority, provenance, identity, evidence, uncertainty, limitation, and boundary disclosure verification against real regenerated artifacts
- Independently verifies determinism (two fresh generations byte-identical modulo timestamps) and read-only guarantees (checksum comparison before/after)
- Independently probes all ten named fail-closed conditions and re-runs the full regression suite, compileall, and fast_green
- Classifies every finding as genuine implementation defect, documentation issue, architectural clarification, or no defect; repairs and documents only genuine implementation defects
- No schema changes, reasoning, inference, Decision Evaluation, Execution Planning, or execution capability introduced; runtime remains Observed/observe/execution-unavailable; PFN-001 satisfied

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-10T14:53:13.853854+02:00
