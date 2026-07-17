# Task Contract

## Task ID

20260717-1533-phase-136z-stage-3-typed-authority-model-shared-core-implementation

## Title

Phase 136Z: Stage 3 Typed Authority Model Shared Core Implementation

## Status

active

## Mode

implementation

## Goal

Phase 136Z: Stage 3 Typed Authority Model Shared Core Implementation

## Allowed Files

- src/pcae/cltr/authority/**
- tests/test_cltr_authority_136z_shared_core.py
- tests/test_cltr_cutover_136m_request_and_readiness_independent_verification.py
- docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_SHARED_CORE_IMPLEMENTATION.md
- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md

## Forbidden Files

- src/pcae/cltr/models.py
- src/pcae/cltr/digest.py
- src/pcae/cltr/canonicalization.py
- src/pcae/cltr/enums.py
- src/pcae/schema_resources/**

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

- Shared-core primitives only (Group 1): ABSENT sentinel, OpaqueJsonValue, immutable containers, extension mapping, enums, identifiers, digests, references, timestamps, limitations/authority-disclosure, envelope, errors, serialization
- No record-family model implemented (AuthorityEpoch etc. deferred to future groups)
- No new production dependency
- No production module imports pcae.cltr.authority
- Wheel/sdist include the new package; installed-wheel smoke test passes

## Acceptance Checks

- python -m pytest tests/test_cltr_authority_136z_shared_core.py -v
- python -m pytest -k cltr_cutover -n auto
- python -m pytest -m fast_green -n auto

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-17T15:33:34.041423+02:00
