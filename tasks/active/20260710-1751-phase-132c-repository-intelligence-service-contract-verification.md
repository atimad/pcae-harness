# Task Contract

## Task ID

20260710-1751-phase-132c-repository-intelligence-service-contract-verification

## Title

Phase 132C Repository Intelligence Service Contract Verification

## Status

active

## Mode

verification

## Goal

Independently verify the 132B contract by re-deriving every requirement directly from 132A architecture, Tracks 119-131 architecture and implementation, Unified Query's real source, and Repository Intelligence artifacts -- not from 132B's own prose. Verify purpose, scope, authority, consumer, lifecycle, request, response, composition, provenance, evidence, identity, boundary, determinism, failure (specifically re-deriving the silent-omission-as-BLOCKING treatment from 131F), governance, compatibility, extensibility, and versioning. Produce a verdict table (CONFIRMED/NON-BLOCKING/BLOCKING); repair only genuine blocking defects. No implementation, no schema changes, no source/test code changes, no runtime behavior changes.

## Allowed Files

- docs/PHASE_132_REPOSITORY_INTELLIGENCE_SERVICE_CONTRACT_VERIFICATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md

## Forbidden Files

- TBD


## Allowed Zones

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

- Independently re-derives purpose, scope (no hidden expansion), authority (no leakage), consumer (conceptual only), and lifecycle (nine stages, no hidden/reordered stages) directly from 132A and real Unified Query source, not 132B prose
- Independently re-derives request/response/composition/provenance/evidence/identity/boundary contracts against real Unified Query source and schema files, cross-checked for internal consistency
- Independently re-derives determinism, failure (specifically confirming silent omission is now a BLOCKING contract violation per 131F), governance, compatibility (Tracks 119-131), extensibility, and versioning
- Produces a verdict table classifying each finding CONFIRMED/NON-BLOCKING/BLOCKING; repairs only genuine blocking defects; re-evaluates inherited technical debt without repairing unless genuinely blocking
- Confirms PFN-001, no implementation occurred, no runtime behavior changed, execution remains unavailable; recommends 132D next

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-10T17:51:53.070408+02:00
