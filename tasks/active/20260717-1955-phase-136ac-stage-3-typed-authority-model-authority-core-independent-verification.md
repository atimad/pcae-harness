# Task Contract

## Task ID

20260717-1955-phase-136ac-stage-3-typed-authority-model-authority-core-independent-verification

## Title

Phase 136AC: Stage 3 Typed Authority Model Authority Core Independent Verification

## Status

active

## Mode

implementation

## Goal

Independently re-derive and verify the Phase 136AB Authority Core (AuthorityEpoch/AuthorityState) typed models against the frozen Stage 3 contracts and executable schemas; document findings and verdict.

## Allowed Files

- tests/test_cltr_authority_136ac_authority_core_independent.py
- src/pcae/cltr/authority/authority_core.py
- docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_AUTHORITY_CORE_INDEPENDENT_VERIFICATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json

## Forbidden Files

- src/pcae/cltr/authority/request_readiness.py


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

- TBD

## Acceptance Criteria

- No later record-family model (CutoverRequest/ReadinessPackage/etc.) introduced
- No semantic validator, repository, persistence, or authority resolver introduced
- No production runtime import into pcae.cltr.authority
- Independent test module constructs expectations from frozen contracts/schemas, not from 136AB fixtures

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest tests/test_cltr_authority_136ac_authority_core_independent.py -v passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-17T19:55:09.324731+02:00
