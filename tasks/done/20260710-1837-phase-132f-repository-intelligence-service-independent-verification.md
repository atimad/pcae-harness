# Task Contract

## Task ID

20260710-1837-phase-132f-repository-intelligence-service-independent-verification

## Title

Phase 132F Repository Intelligence Service Independent Verification

## Status

done

## Mode

verification

## Goal

Independently verify the 132E Repository Intelligence Service implementation against 132A architecture, 132B contract, 132D plan, and Tracks 119-131 -- re-deriving conformance from source and fresh-generated artifacts, never trusting 132E's own tests or report. Verify all nine lifecycle stages, Unified Query reuse, composition, composite requests, response assembly, provenance, evidence, boundary disclosure, identity, and failure behavior with fresh edge-case probes beyond the dedicated 132E regression suite -- specifically extending the 131F silent-omission defect class (complete miss, partial miss, nested composite miss, empty-success scenarios, hidden omission paths). Produce a verdict table (CONFIRMED/NON-BLOCKING/BLOCKING); repair only genuine blocking defects. No new functionality, no Unified Query modification, no schema changes, no runtime behavior changes.

## Allowed Files

- docs/PHASE_132_REPOSITORY_INTELLIGENCE_SERVICE_VERIFICATION.md
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

- Independently re-derives architecture/contract conformance from 132A/132B and real source, not from 132E's own report; verifies all nine lifecycle stages with no hidden stages; verifies Unified Query reuse (no duplicated routing/identity/artifact-loading)
- Independently verifies composition (deterministic, no reinterpretation/inference/knowledge-creation/evidence-strengthening), composite requests (independent, non-correlating), response assembly (composition_metadata structurally separate from provenance), boundary disclosure reuse, and identity reuse using fresh probes against freshly generated artifacts
- Designs and runs NEW fresh edge-case probes beyond 132E's own 50-test suite -- specifically extending the 131F silent-omission defect class: complete miss, partial miss, nested composite miss, empty-success scenarios, hidden omission paths; confirms every path produces explicit disclosure, treating any silent empty success as BLOCKING
- Verifies read-only guarantees, determinism, CLI behavior, Track 119-132 regression, and governance; runs 132E's 50 tests, Track 121-132 regression, fast_green, and compileall, confirming all remain green; produces a verdict table (CONFIRMED/NON-BLOCKING/BLOCKING)
- Confirms PFN-001, no implementation changes occurred except any genuine blocking repair, no runtime behavior changed outside the Service, execution remains unavailable; delivers an overall Track 132 completion assessment and next-chapter context

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-10T18:37:46.803686+02:00
