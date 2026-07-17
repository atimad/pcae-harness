# Task Contract

## Task ID

20260717-0537-phase-136t-notification-marker-receipt-authority-binding-schema-implementation

## Title

Phase 136T: Notification/Marker/Receipt Authority Binding Schema Implementation

## Status

active

## Mode

implementation

## Goal

Implement CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0 Implementation Group 10 (NotificationAuthorityBinding, MarkerAuthorityBinding, FinalizationReceiptAuthorityBinding) executable schemas, manifest entries, fixtures, and focused tests, per the frozen contract's Sec.46 grouping. Group 9 (ReconciliationResult/HistoricalAuthorityReference) has no schema file and is therefore not part of the executable-schema implementation track; Group 10 is the next contract-conformant deliverable.

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- src/pcae/schema_resources/cltr_cutover/manifest.json
- src/pcae/schema_resources/cltr_cutover/records/*
- src/pcae/schema_resources/cltr_cutover/records/**
- src/pcae/schema_resources/cltr_cutover/README.md
- src/pcae/schema_resources/__init__.py
- tests/test_cltr_cutover_136t_*.py
- tests/fixtures/cltr_cutover/records/notification_authority_binding/**
- tests/fixtures/cltr_cutover/records/marker_authority_binding/**
- tests/fixtures/cltr_cutover/records/receipt_authority_binding/**
- tests/test_cltr_cutover_136h_shared_core.py
- tests/test_cltr_cutover_136i_shared_core_independent_verification.py
- tests/test_cltr_cutover_136j_authority_core.py
- tests/test_cltr_cutover_136k_authority_core_independent_verification.py
- tests/test_cltr_cutover_136l_request_and_readiness.py
- tests/test_cltr_cutover_136m_request_and_readiness_independent_verification.py
- tests/test_cltr_cutover_136n_authorization_and_candidate.py
- tests/test_cltr_cutover_136o_authorization_and_candidate_independent_verification.py
- tests/test_cltr_cutover_136p_publication_schema.py
- tests/test_cltr_cutover_136q_publication_schema_independent_verification.py
- tests/test_cltr_cutover_136r_recovery_schema.py
- tests/test_cltr_cutover_136s_recovery_schema_independent_verification.py
- tests/test_schema_runtime_boundaries.py
- tests/test_schema_runtime_packaging.py
- docs/PHASE_136_NOTIFICATION_MARKER_RECEIPT_BINDING_SCHEMA_IMPLEMENTATION.md
- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json

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

- TBD

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-17T05:37:30.230952+02:00
