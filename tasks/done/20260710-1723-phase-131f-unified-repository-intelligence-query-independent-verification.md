# Task Contract

## Task ID

20260710-1723-phase-131f-unified-repository-intelligence-query-independent-verification

## Title

Phase 131F Unified Repository Intelligence Query Independent Verification

## Status

done

## Mode

verification

## Goal

Independently verify the 131E Unified Query implementation against 131A architecture, 131B contract, 131D plan, and existing Repository Intelligence contracts -- re-deriving conformance from source and fresh-generated artifacts, never trusting 131E's own tests or report. Verify all nine lifecycle stages, routing, artifact resolution, identity, provenance, evidence, boundary disclosure, failure behavior, read-only guarantees, determinism, CLI, and Track 119-130 regression. Independently classify the 131E-discovered Change Impact/Advisory Context schema divergence. Produce a verdict table (CONFIRMED/NON-BLOCKING/BLOCKING); repair only genuine blocking defects. No implementation, no schema changes, no expanded Query capabilities, no runtime behavior changes.

## Allowed Files

- docs/PHASE_131_UNIFIED_REPOSITORY_INTELLIGENCE_QUERY_VERIFICATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- src/pcae/repository_intelligence/unified_query/unified_query_engine.py
- tasks/active/20260710-1723-phase-131f-unified-repository-intelligence-query-independent-verification.md

## Forbidden Files

- TBD


## Allowed Zones

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

- Independently re-derives architecture/contract conformance from 131A/131B text and real source, not from 131E's own report; verifies all nine lifecycle stages exist and execute in correct sequence with no hidden stages
- Independently verifies routing (deterministic, explicit tables, allow-list enforcement, fail-closed), artifact resolution (reuses Track 121/130, no duplicated identity logic), identity (exact match only, explicit unresolved, no fuzzy/alias/probabilistic/silent-merge), and response assembly (no synthesized conclusions) using fresh scripts against freshly generated artifacts
- Independently verifies provenance completeness, evidence preservation, boundary disclosure reuse of the real nine-field schema, fail-closed failure behavior, read-only guarantees, determinism, and CLI behavior; classifies the 131E-discovered schema divergence without repairing it unless genuinely blocking
- Runs 131E's 43 tests, Track 121/122/123/130 regression (86 tests), fast_green, and compileall, confirming all remain green; produces a verdict table (CONFIRMED/NON-BLOCKING/BLOCKING)
- Confirms PFN-001, no implementation changes occurred, no runtime behavior changed outside the query subsystem, execution remains unavailable; delivers an overall Track 131 completion assessment and next-chapter recommendation

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-10T17:23:46.684792+02:00
