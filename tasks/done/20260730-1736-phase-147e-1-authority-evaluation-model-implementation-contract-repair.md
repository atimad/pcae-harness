# Task Contract

## Task ID

20260730-1736-phase-147e-1-authority-evaluation-model-implementation-contract-repair

## Title

Phase 147E.1: Authority Evaluation Model Implementation Contract Repair

## Status

done

## Mode

implementation

## Goal

Repair BF-147F-1 in AEMIC-001 (Phase 147F's Blocking finding: evaluate()'s closed signature had no channel for citation_text, making the citation_text if-and-only-if invariant unsatisfiable for the eligible case). Add citation_text as evaluate()'s own fifth parameter, enforced at construction time; reject widening EligibleAuthorityDeclaration as foreclosed by AEM-001's own closed-shape freeze. Contract-repair only; no production code, test, schema, or other contract modified; no implementation authorized.

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- docs/contracts/AUTHORITY_EVALUATION_MODEL_IMPLEMENTATION_CONTRACT.md
- docs/PHASE_147E.1_AUTHORITY_EVALUATION_MODEL_IMPLEMENTATION_CONTRACT_REPAIR.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- .pcae/phase-reports/**

## Forbidden Files

- TBD


## Allowed Zones

- TBD

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

- Phase 147E.1 report produced with all required sections
- AEMIC-001 repaired to v1.1, BF-147F-1 resolved, no other requirement narrowed
- No src/pcae/**, tests/**, schema, or any other existing contract file modified

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-30T17:36:49.885481+02:00
