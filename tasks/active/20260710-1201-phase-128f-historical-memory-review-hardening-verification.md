# Task Contract

## Task ID

20260710-1201-phase-128f-historical-memory-review-hardening-verification

## Title

Phase 128F Historical Memory Review Hardening Verification

## Status

active

## Mode

verification

## Goal

Independently verify the completed 128E Historical Memory hardening implementation, re-deriving every check directly from source, freshly generated artifacts, and real repository state -- not by trusting 128E's implementation, comments, documentation, tests, or reports. Documentation only: no source, schema, or test code change unless a genuine defect is found and verified, in which case only that verified defect may be repaired.

## Allowed Files

- docs/PHASE_128_HISTORICAL_MEMORY_REVIEW_HARDENING_VERIFICATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/20260710-1201-phase-128f-historical-memory-review-hardening-verification.md
- src/pcae/repository_intelligence/historical_memory/historical_builder.py

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

- Independently verifies both 128E hardening items (identifier-order clarification comment exists with unchanged executable logic; historical_generator.py explicitly documented; frozen contracts unchanged)
- Freshly generates a Historical Memory artifact (not reused) and independently verifies determinism via two independent generations, byte-identical modulo approved timestamp fields
- Independently verifies schema conformance (zero violations), serialization compatibility, temporal semantics, evidence/attribution/limitation/boundary propagation, and read-only guarantees via checksum comparison
- Independently probes fail-closed behavior and runs full regression suites (Historical Memory, DKG, Change Impact, Advisory Context, Query Layer, RKS), fast_green, and compileall
- Runs governance validation and confirms no runtime behavior changed and execution remains unavailable
- No source, schema, or test code modified unless a genuine verified defect is found, in which case only that defect is repaired and the full verification is re-run

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-10T12:01:10.003884+02:00
