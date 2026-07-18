# Task Contract

## Task ID

20260718-0640-phase-136ag-stage-3-typed-authority-model-authorization-and-candidate-independent-verification

## Title

Phase 136AG: Stage 3 Typed Authority Model Authorization and Candidate Independent Verification

## Status

active

## Mode

implementation

## Goal

Independently verify HumanAuthorization, CutoverCandidate, and Certification typed record models from Phase 136AF against frozen contracts and live executable schemas; bounded repair of reproduced Blocking defects only.

## Allowed Files

- tests/test_cltr_authority_136ag_authorization_candidate_independent.py
- src/pcae/cltr/authority/authorization_candidate.py
- docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_AUTHORIZATION_CANDIDATE_INDEPENDENT_VERIFICATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-metadata-repairs.log
- .pcae/phase-reports/**

## Forbidden Files

- src/pcae/cltr/authority/publication.py
- src/pcae/cltr/authority/recovery.py
- src/pcae/cltr/authority/bindings.py
- src/pcae/cltr/authority/compatibility_quarantine.py

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

- All three record contracts independently re-derived from frozen contracts and live schemas, not from 136AF tests/fixtures/prose
- No later record-family model introduced; no authentication, authorization evaluation, candidate eligibility, or certification verification introduced
- No unresolved Blocking finding remains

## Acceptance Checks

- New independent test module passes
- 136AF/136AE/136AD/136AC/136AB/136AA/136Z focused suites pass with no new failures
- Fresh wheel/sdist build and isolated install verification passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-18T06:40:52.549542+02:00
