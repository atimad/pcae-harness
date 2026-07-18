# Task Contract

## Task ID

20260719-0137-phase-136at-stage-3-typed-authority-model-quarantinerecord-implementation

## Title

Phase 136AT: Stage 3 Typed Authority Model QuarantineRecord Implementation

## Status

active

## Mode

implementation

## Goal

Implement the QuarantineRecord record-family model (Typed Model Implementation Group 11) exactly as defined by frozen contracts and the live executable schema; representation only, no quarantine behavior.

## Allowed Files

- tests/test_cltr_authority_136at_quarantine_record.py
- src/pcae/cltr/authority/compatibility_quarantine.py
- src/pcae/cltr/authority/__init__.py
- tests/test_cltr_authority_136aa_shared_core_independent.py
- tests/test_cltr_authority_136ab_authority_core.py
- tests/test_cltr_authority_136ac_authority_core_independent.py
- tests/test_cltr_authority_136ad_request_readiness.py
- tests/test_cltr_authority_136ae_request_readiness_independent.py
- tests/test_cltr_authority_136af_authorization_candidate.py
- tests/test_cltr_authority_136ag_authorization_candidate_independent.py
- tests/test_cltr_authority_136ah_publication.py
- tests/test_cltr_authority_136ai_publication_independent.py
- tests/test_cltr_authority_136aj_recovery_concurrency.py
- tests/test_cltr_authority_136ak_recovery_concurrency_independent.py
- tests/test_cltr_authority_136al_notification_authority_binding.py
- tests/test_cltr_authority_136am_notification_authority_binding_independent.py
- tests/test_cltr_authority_136an_marker_authority_binding.py
- tests/test_cltr_authority_136ao_marker_authority_binding_independent.py
- tests/test_cltr_authority_136ap_finalization_receipt_authority_binding.py
- tests/test_cltr_authority_136aq_finalization_receipt_authority_binding_independent.py
- tests/test_cltr_authority_136ar_compatibility_state.py
- tests/test_cltr_authority_136as_compatibility_state_independent.py
- tests/test_cltr_authority_136z_shared_core.py
- docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_QUARANTINE_RECORD_IMPLEMENTATION.md
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

- TBD

## Acceptance Criteria

- QuarantineRecord record contract implemented exactly per frozen contracts/live schema; representation only
- CompatibilityState behavior unchanged; sixteen total record-family models exported
- No quarantine operation, reference lookup, authority activation, or lifecycle mutation introduced

## Acceptance Checks

- New dedicated 136AT test module passes
- All test_cltr_authority_136*/test_cltr_cutover_136* modules pass with no new failures
- Fresh wheel/sdist build and isolated install verification passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-19T01:37:16.150929+02:00
