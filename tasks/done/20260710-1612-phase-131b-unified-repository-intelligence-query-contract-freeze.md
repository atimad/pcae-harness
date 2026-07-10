# Task Contract

## Task ID

20260710-1612-phase-131b-unified-repository-intelligence-query-contract-freeze

## Title

Phase 131B Unified Repository Intelligence Query Contract Freeze

## Status

done

## Mode

architecture

## Goal

Freeze the binding contract governing 131C-131F: transform 131A's architecture into a formal contract covering purpose, scope (six existing artifact families, no expansion), authority, query responsibility, routing, response, provenance, evidence, identity, cross-artifact, determinism, read-only, failure, boundary disclosure, compatibility, governance, and versioning. Perform an internal consistency review and a technical debt review (re-evaluate 131A's handoff-timestamp finding and known tooling debt, repair only if a genuine blocking architectural issue is found). No implementation, no schema changes, no source/test code changes, no runtime behavior changes.

## Allowed Files

- docs/PHASE_131_UNIFIED_REPOSITORY_INTELLIGENCE_QUERY_CONTRACT_FREEZE.md
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

- Freezes purpose, scope (six existing artifact families, no expansion), authority, query responsibility (may: locate/correlate/aggregate/expose/reference; never: infer/reason/recommend/rank/evaluate/authorize/mutate/execute), and routing (declared responsibilities only, no heuristics/optimization/indexing) contracts
- Freezes response (derivative, no synthesized conclusions), provenance (six mandatory elements), evidence (never strengthens/transforms/infers), identity (existing stable identifiers only, no alias/fuzzy/heuristic/probabilistic/silent-merge), and cross-artifact (consumes but never replaces Track 130) contracts
- Freezes determinism, read-only, failure (fail-closed, no inferred recovery, no silent omission), boundary disclosure, compatibility (Tracks 119-130), governance (observe-only, execution unavailable, reproducibility, explainability, auditability, PFN-001), and versioning contracts
- Performs internal consistency review across authority/routing/provenance/identity/evidence/determinism/failure/compatibility documenting ambiguity without repairing it; re-evaluates 131A's handoff-timestamp finding and known tooling debt without repairing unless a genuine blocking architectural issue is found
- Confirms PFN-001, no implementation occurred, no runtime behavior changed, execution remains unavailable; recommends 131C next

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-10T16:12:10.561374+02:00
