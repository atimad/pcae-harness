# Task Contract

## Task ID

20260710-1642-phase-131e-unified-repository-intelligence-query-prototype

## Title

Phase 131E Unified Repository Intelligence Query Prototype

## Status

active

## Mode

implementation

## Goal

Implement the first deterministic, read-only Unified Repository Intelligence Query prototype exactly as scoped by 131A-131D: a new src/pcae/repository_intelligence/unified_query/ package implementing the 9-stage lifecycle, deterministic routing (single-family, explicitly-enumerated multi-family, unresolved, unsupported), artifact resolution reusing Track 130 identity logic, response assembly preserving provenance/evidence/uncertainty/limitations/boundary disclosures with no synthesized conclusions, boundary disclosure mapping onto the real nine-field schema, complete six-element provenance, fail-closed failure handling, governed CLI wiring, and focused tests. No schema changes, no modification to any existing Track 119-130 source file, no reasoning/ranking/execution capability introduced.

## Allowed Files

- src/pcae/repository_intelligence/unified_query/__init__.py
- src/pcae/repository_intelligence/unified_query/errors.py
- src/pcae/repository_intelligence/unified_query/request.py
- src/pcae/repository_intelligence/unified_query/routing.py
- src/pcae/repository_intelligence/unified_query/identity.py
- src/pcae/repository_intelligence/unified_query/artifact_loading.py
- src/pcae/repository_intelligence/unified_query/provenance.py
- src/pcae/repository_intelligence/unified_query/boundary.py
- src/pcae/repository_intelligence/unified_query/response.py
- src/pcae/repository_intelligence/unified_query/unified_query_engine.py
- src/pcae/cli.py
- src/pcae/commands/repository_intelligence.py
- tests/test_phase_131e_unified_repository_intelligence_query_prototype.py
- docs/PHASE_131_UNIFIED_REPOSITORY_INTELLIGENCE_QUERY_PROTOTYPE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/20260710-1642-phase-131e-unified-repository-intelligence-query-prototype.md

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

- Implements a new, additive src/pcae/repository_intelligence/unified_query/ package with no modification to any existing Track 119-130 source file or schema; implements the full 9-stage query lifecycle
- Implements deterministic routing (single-family, explicitly-enumerated multi-family, unresolved, unsupported), artifact resolution reusing Track 130 identity logic exactly (exact match, explicit unresolved state, no fuzzy/alias/probabilistic/silent-merge), and derivative response assembly with no synthesized conclusions
- Implements complete six-element provenance attachment, verbatim evidence preservation, boundary disclosure mapping onto the real nine-field schema, and fail-closed failure handling per the planned exception model
- Adds governed CLI wiring and focused tests covering all required areas (normalization, routing, single/multi-family, unresolved/unsupported routing, identity, provenance, evidence, uncertainty, limitations, boundary disclosures, determinism, fail-closed behavior, read-only guarantees, compatibility); runs full affected test suites confirming Track 121/130 regression-free
- Confirms PFN-001, no schema changed, no runtime behavior changed outside the new query subsystem, execution remains unavailable; recommends 131F next

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-10T16:42:13.663754+02:00
