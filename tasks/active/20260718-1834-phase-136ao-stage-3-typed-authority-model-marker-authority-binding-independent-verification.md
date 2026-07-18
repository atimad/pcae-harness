# Task Contract

## Task ID

20260718-1834-phase-136ao-stage-3-typed-authority-model-marker-authority-binding-independent-verification

## Title

Phase 136AO: Stage 3 Typed Authority Model Marker Authority Binding Independent Verification

## Status

active

## Mode

implementation

## Goal

Independently re-derive and verify MarkerAuthorityBinding typed record model from Phase 136AN against frozen contracts and live executable schemas; bounded repair of independently reproduced Blocking defects only.

## Allowed Files

- tests/test_cltr_authority_136ao_marker_authority_binding_independent.py
- src/pcae/cltr/authority/bindings.py
- docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_MARKER_AUTHORITY_BINDING_INDEPENDENT_VERIFICATION.md
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

- TBD

## Acceptance Criteria

- MarkerAuthorityBinding record contract independently re-derived from frozen contracts and live schemas, not from 136AN tests/fixtures/prose
- No later record-family model introduced; no marker management, authority activation, or lifecycle mutation introduced
- No unresolved Blocking finding remains

## Acceptance Checks

- New independent test module passes
- 136AN/136AM/136AL/136AK/136AJ/136AI/136AH/136AG/136AF/136AE/136AD/136AC/136AB/136AA/136Z focused suites pass with no new failures
- Fresh wheel/sdist build and isolated install verification passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-18T18:34:50.605605+02:00
