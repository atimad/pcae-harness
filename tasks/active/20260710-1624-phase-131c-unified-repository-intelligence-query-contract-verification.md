# Task Contract

## Task ID

20260710-1624-phase-131c-unified-repository-intelligence-query-contract-verification

## Title

Phase 131C Unified Repository Intelligence Query Contract Verification

## Status

active

## Mode

verification

## Goal

Independently verify the 131B contract by re-deriving every requirement directly from 131A architecture, Track 119 executable schemas, Tracks 120-130 source code, and current repository state -- not from 131B's own prose. Produce a verdict (CONFIRMED/NON-BLOCKING/BLOCKING) for authority, routing, provenance, evidence, identity, cross-artifact, determinism, read-only, failure, boundary, compatibility, governance, and versioning. Repair only genuine blocking defects. Re-evaluate known technical debt without repairing unless genuinely blocking. No implementation, no schema changes, no source/test code changes, no runtime behavior changes.

## Allowed Files

- docs/PHASE_131_UNIFIED_REPOSITORY_INTELLIGENCE_QUERY_CONTRACT_VERIFICATION.md
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

- Independently re-derives purpose, scope (six artifact families, no hidden expansion), authority (no leakage), and responsibility (may/never lists) directly from 131A architecture and current source, not 131B prose
- Independently re-derives routing, response, provenance (six elements), evidence, identity (cross-checked against DKG/Historical Memory/Cross-Artifact Integration source), cross-artifact, determinism, read-only, failure, boundary, compatibility, governance, and versioning
- Produces a verdict table classifying each finding CONFIRMED/NON-BLOCKING/BLOCKING; repairs only genuine blocking defects; carries forward only genuine findings
- Re-evaluates known technical debt (bootstrap timestamp, stale phase-completion metadata, report ordering, phase-id comparison, persistence naming) independently, without repairing unless genuinely blocking
- Confirms PFN-001, no implementation occurred, no runtime behavior changed, execution remains unavailable; recommends 131D next

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-10T16:24:37.212105+02:00
