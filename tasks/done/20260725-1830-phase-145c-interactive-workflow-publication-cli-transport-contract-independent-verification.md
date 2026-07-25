# Task Contract

## Task ID

20260725-1830-phase-145c-interactive-workflow-publication-cli-transport-contract-independent-verification

## Title

Phase 145C: Interactive Workflow + Publication CLI/Transport Contract Independent Verification

## Status

done

## Mode

validation

## Goal

Independently re-derive and verify IWPC-001 v1.0 from first principles and existing governing contracts. Adversarial independent verification: identify Blocking, Non-Blocking, Observation, and Deferred findings; repair only demonstrated Blocking defects. No CLI command, transport adapter, SessionRepository concrete class, or Pending-Readiness Store concrete class implemented. No production code under src/pcae/interactive_workflow/** or src/pcae/governance/publication/** modified. Runtime remains Observed / observe / unavailable.

## Allowed Files

- docs/PHASE_145C_INTERACTIVE_WORKFLOW_PUBLICATION_CLI_TRANSPORT_CONTRACT_INDEPENDENT_VERIFICATION.md
- docs/contracts/INTERACTIVE_WORKFLOW_PUBLICATION_CLI_TRANSPORT_CONTRACT.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/TODO.md
- tasks/DECISIONS.md
- tasks/active/**
- tasks/done/**
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- src/pcae/interactive_workflow/**
- src/pcae/governance/publication/**
- src/pcae/commands/**
- docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md
- docs/contracts/PUBLICATION_EXECUTION_CONTRACT.md
- docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md
- docs/contracts/TYPED_AUTHORITY_MODEL_CONSUMPTION_CONTRACT.md
- docs/contracts/TYPED_AUTHORITY_MODEL_PRODUCTION_CONSUMPTION_CONTRACT.md

## Allowed Zones

- docs
- tasks
- policy
- config

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

strict

## Forbidden Changes

- No CLI/transport/store implementation
- No production code modification
- No runtime capability change

## Acceptance Criteria

- IWPC-001 independently re-derived across all 31 sections
- Requirement numbering/count independently re-verified (191, sequential, no gaps/dupes)
- One demonstrated Blocking finding repaired via in-place minor version bump (v1.0 -> v1.1), matching this repository's established narrow-repair precedent (Phase 138C.1, Phase 137M, Phase 143I.1)
- Runtime remains Observed / observe / unavailable

## Acceptance Checks

- pcae check passes
- pcae health passes
- pcae doctor execution-chain passes
- pcae push check clean
- pcae runtime inspect unchanged before/after
- fast_green test suite passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-25T18:30:00.000000+02:00
