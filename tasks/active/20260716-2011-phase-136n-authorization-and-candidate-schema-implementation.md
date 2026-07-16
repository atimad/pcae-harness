# Task Contract

## Task ID

20260716-2011-phase-136n-authorization-and-candidate-schema-implementation

## Title

Phase 136N: Authorization and Candidate Schema Implementation

## Status

active

## Mode

implementation

## Goal

Implement CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0 Implementation Group 4 (HumanAuthorization, CutoverCandidate, Certification) executable schemas, manifest entries, bounded shared cas_expectation definition, fixtures, and focused tests, per the frozen contract and 136E implementation plan.

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- src/pcae/schema_resources/cltr_cutover/manifest.json
- src/pcae/schema_resources/cltr_cutover/shared/references.schema.json
- src/pcae/schema_resources/cltr_cutover/shared/digest.schema.json
- src/pcae/schema_resources/cltr_cutover/records/*
- src/pcae/schema_resources/cltr_cutover/records/**
- src/pcae/schema_resources/cltr_cutover/README.md
- src/pcae/schema_resources/__init__.py
- tests/test_cltr_cutover_136n_authorization_and_candidate.py
- tests/test_cltr_cutover_136h_shared_core.py
- tests/test_cltr_cutover_136i_shared_core_independent_verification.py
- tests/test_cltr_cutover_136j_authority_core.py
- tests/test_cltr_cutover_136k_authority_core_independent_verification.py
- tests/test_cltr_cutover_136l_request_and_readiness.py
- tests/test_cltr_cutover_136m_request_and_readiness_independent_verification.py
- tests/test_schema_runtime_boundaries.py
- tests/test_schema_runtime_packaging.py
- docs/PHASE_136_AUTHORIZATION_AND_CANDIDATE_SCHEMA_IMPLEMENTATION.md
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

- TBD

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-16T20:11:46.017502+02:00
