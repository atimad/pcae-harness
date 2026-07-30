# Task Contract

## Task ID

20260730-1947-phase-147e-2-authority-evaluation-model-implementation-contract-second-repair

## Title

Phase 147E.2: Authority Evaluation Model Implementation Contract Second Repair

## Status

done

## Mode

implementation

## Goal

Repair BF-147F.1-1 in AEMIC-001 (Phase 147F.1's Blocking finding: AuthorityEvaluationOutcome.template_ref/.template_version are mandatory for every EvaluationResult branch but evaluate()'s own signature had no channel for them, making the INDETERMINATE branch unconstructible). Add template_ref/template_version as evaluate()'s own first two parameters, with a new TemplateIdentityMismatchError enforcing agreement with a resolved Declaration's own identity. Contract-repair only; no production code, test, schema, or other contract modified; no implementation authorized.

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- docs/contracts/AUTHORITY_EVALUATION_MODEL_IMPLEMENTATION_CONTRACT.md
- docs/PHASE_147E.2_AUTHORITY_EVALUATION_MODEL_IMPLEMENTATION_CONTRACT_SECOND_REPAIR.md
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

- Phase 147E.2 report produced with all required sections
- AEMIC-001 repaired to v1.2, BF-147F.1-1 resolved, no other requirement narrowed
- No src/pcae/**, tests/**, schema, or any other existing contract file modified

## Acceptance Checks

- pcae check passes
- pcae health passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-30T19:47:00.938663+02:00
