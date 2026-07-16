# Task Contract

## Task ID

20260717-0052-phase-136q-publication-schema-independent-verification

## Title

Phase 136Q: Publication Schema Independent Verification

## Status

done

## Mode

verification

## Goal

Independently re-derive and verify Implementation Group 5 (PublicationAttempt, PublicationEvidence) executable schemas against CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0's frozen primary contract; produce the 136Q independent-verification document, freshly-authored adversarial tests, and canonical finalization artifacts. No recovery-schema implementation, bindings, typed models, semantic validation, persistence, authority resolution, or execution capability.

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- docs/PHASE_136_PUBLICATION_SCHEMA_INDEPENDENT_VERIFICATION.md
- tests/test_cltr_cutover_136q_publication_schema_independent_verification.py
- tests/fixtures/cltr_cutover/records/publication_attempt/**
- tests/fixtures/cltr_cutover/records/publication_evidence/**
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

- Exact Group 5 inventory independently re-derived from Section 46 and confirmed as PublicationAttempt + PublicationEvidence only
- ConcurrencyConflict exclusion independently confirmed; correct later contract group (8) identified
- Field tables, CAS expectation embedding, dependency graph, manifest, packaging, no-network/no-authority/no-execution independently verified
- Zero unresolved Blocking findings, or bounded repair with regression evidence

## Acceptance Checks

- pytest tests/test_cltr_cutover_136q_publication_schema_independent_verification.py
- pytest -m fast_green

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-17T00:52:57.661933+02:00
