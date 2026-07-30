# Task Contract

## Task ID

20260730-1851-phase-147f-1-authority-evaluation-model-implementation-contract-independent-re-verification

## Title

Phase 147F.1: Authority Evaluation Model Implementation Contract Independent Re-Verification

## Status

active

## Mode

implementation

## Goal

Independently re-verify AEMIC-001 v1.1 against AEM-001, Phase 147C/147D/147F/147E.1, IWC-001, IWPC-001, PEC-001, CHGR-001, TAMC-001/TAMPC-001, GAC-001, and direct source reinspection. Documentation-only; no production code, test, schema, or existing contract file modified; no implementation authorized. Includes 147F.1R canonical-report and finalization recovery: the substantive verification document and task transition were completed in a prior session, but pcae phase complete, metadata sync, commit, push, and terminal notification were never invoked; this recovery completes that governed lifecycle without altering any substantive finding.

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- docs/PHASE_147F.1_AUTHORITY_EVALUATION_MODEL_IMPLEMENTATION_CONTRACT_INDEPENDENT_REVERIFICATION.md
- docs/PHASE_147F.1R_CANONICAL_REPORT_AND_FINALIZATION_RECOVERY.md
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

strict

## Forbidden Changes

- No runtime invocation
- No prompt execution
- No source behavior changes outside task/session/handoff governance
- No execution authorization
- No commit
- No push
- No rollback

## Acceptance Criteria

- TBD

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-30T18:51:27.550605+02:00
