# Task Contract

## Task ID

20260710-1807-phase-132e-repository-intelligence-service-prototype

## Title

Phase 132E Repository Intelligence Service Prototype

## Status

active

## Mode

implementation

## Goal

Implement the first deterministic, read-only Repository Intelligence Service prototype exactly as scoped by 132A-132D: a new src/pcae/repository_intelligence/service/ package implementing the 9-stage lifecycle, exclusively reusing Unified Query's real execute_unified_query entry point (no duplicated routing/identity/artifact-loading), deterministic composition (merge, never reinterpret/infer/strengthen/create knowledge), bounded non-correlating composite requests, response assembly with a structurally-separated composition_metadata field, boundary disclosure reuse of the real nine-field object, fail-closed failure handling explicitly preserving the Track 131/132 silent-omission invariant, governed CLI wiring, and focused tests including a silent-omission regression test. No schema changes, no modification to any existing Track 119-131 source file, no reasoning/ranking/execution capability introduced.

## Allowed Files

- src/pcae/repository_intelligence/service/__init__.py
- src/pcae/repository_intelligence/service/errors.py
- src/pcae/repository_intelligence/service/request.py
- src/pcae/repository_intelligence/service/response.py
- src/pcae/repository_intelligence/service/service_engine.py
- src/pcae/cli.py
- src/pcae/commands/repository_intelligence.py
- tests/test_phase_132e_repository_intelligence_service_prototype.py
- docs/PHASE_132_REPOSITORY_INTELLIGENCE_SERVICE_PROTOTYPE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/20260710-1807-phase-132e-repository-intelligence-service-prototype.md

## Forbidden Files

- TBD


## Allowed Zones

- unclassified
- commands
- cli
- tests
- docs
- tasks

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

- Implements a new, additive src/pcae/repository_intelligence/service/ package with no modification to any existing Track 119-131 source file or schema; implements the full 9-stage lifecycle exclusively via Unified Query's real execute_unified_query entry point
- Implements deterministic composition (merge/preserve ordering/provenance/evidence/uncertainty/limitations/boundary disclosures; never reinterpret/infer/strengthen/create knowledge), bounded non-correlating composite requests (independent per-target queries only), and a structurally-separated composition_metadata field distinct from per-element provenance
- Implements boundary disclosure reuse of the real nine-field object verbatim, complete identity reuse (zero duplicated identity logic), and fail-closed failure handling for unsupported/malformed/unresolved-entity/unresolved-composition/missing-artifact/Unified-Query-failure conditions, explicitly preserving the silent-omission-is-BLOCKING invariant from 131F/132B
- Adds governed CLI wiring and focused tests covering all required areas including an explicit silent-omission regression test; runs full affected test suites (own tests, Track 119-131 regression, fast_green, compileall) confirming zero regression
- Confirms PFN-001, no schema changed, no runtime behavior changed outside the Repository Intelligence Service, execution remains unavailable; recommends 132F next

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-10T18:07:03.938814+02:00
