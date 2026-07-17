# Task Contract

## Task ID

20260717-0137-phase-136r-recovery-schema-implementation

## Title

Phase 136R: Recovery Schema Implementation

## Status

done

## Mode

implementation

## Goal

Implement CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0 Implementation Group 8 (ConcurrencyConflict, RecoveryJournalEntry) executable schemas, manifest entries, fixtures, and focused tests, per the frozen contract's own Sec.46 grouping (not the task prompt's Group-8-excluding framing; ConcurrencyConflict and RecoveryJournalEntry are one atomic contract group per CSCH-EXEC-REQ-062, confirmed by explicit user direction before coding began).

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
- tests/test_cltr_cutover_136r_recovery_schema.py
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
- tests/test_schema_runtime_boundaries.py
- tests/test_schema_runtime_packaging.py
- docs/PHASE_136_RECOVERY_SCHEMA_IMPLEMENTATION.md
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

2026-07-17T01:37:29.044891+02:00
