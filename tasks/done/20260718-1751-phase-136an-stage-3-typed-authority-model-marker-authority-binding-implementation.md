# Task Contract

## Task ID

20260718-1751-phase-136an-stage-3-typed-authority-model-marker-authority-binding-implementation

## Title

Phase 136AN: Stage 3 Typed Authority Model Marker Authority Binding Implementation

## Status

done

## Mode

implementation

## Goal

Implement Typed Model Implementation Group 8 (MarkerAuthorityBinding only) per the frozen 136Y plan; frozen, immutable, schema-backed, lossless typed representation only; no marker management/authority activation/lifecycle mutation logic.

## Allowed Files

- src/pcae/cltr/authority/bindings.py
- src/pcae/cltr/authority/__init__.py
- tests/test_cltr_authority_136an_marker_authority_binding.py
- tests/test_cltr_authority_136am_notification_authority_binding_independent.py
- tests/test_cltr_authority_136al_notification_authority_binding.py
- tests/test_cltr_authority_136ak_recovery_concurrency_independent.py
- tests/test_cltr_authority_136aj_recovery_concurrency.py
- tests/test_cltr_authority_136ai_publication_independent.py
- tests/test_cltr_authority_136ah_publication.py
- tests/test_cltr_authority_136ag_authorization_candidate_independent.py
- tests/test_cltr_authority_136af_authorization_candidate.py
- tests/test_cltr_authority_136ae_request_readiness_independent.py
- tests/test_cltr_authority_136ad_request_readiness.py
- tests/test_cltr_authority_136ac_authority_core_independent.py
- tests/test_cltr_authority_136ab_authority_core.py
- tests/test_cltr_authority_136aa_shared_core_independent.py
- tests/test_cltr_authority_136z_shared_core.py
- docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_MARKER_AUTHORITY_BINDING_IMPLEMENTATION.md
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

- Exactly one new record-family model implemented: MarkerAuthorityBinding
- No marker creation, write, update, delete, discovery, reconciliation, or authority activation/lifecycle mutation
- No later record-family model (FinalizationReceiptAuthorityBinding, CompatibilityState, QuarantineRecord) implemented

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- focused and adjacent regression suites pass

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-18T17:51:49.405887+02:00
