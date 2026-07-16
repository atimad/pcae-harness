# Task Contract

## Task ID

20260716-2151-phase-136o-authorization-and-candidate-schema-independent-verification

## Title

Phase 136O: Authorization and Candidate Schema Independent Verification

## Status

done

## Mode

implementation

## Goal

Independently verify and adversarially attack the HumanAuthorization, CutoverCandidate, and Certification Group 4 executable schemas from Phase 136N; repair genuine bounded defects only; produce the canonical 136O independent-verification document.

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- src/pcae/schema_resources/cltr_cutover/records/human_authorization.schema.json
- src/pcae/schema_resources/cltr_cutover/records/cutover_candidate.schema.json
- src/pcae/schema_resources/cltr_cutover/records/certification.schema.json
- src/pcae/schema_resources/cltr_cutover/shared/*
- src/pcae/schema_resources/cltr_cutover/manifest.json
- src/pcae/schema_resources/cltr_cutover/README.md
- src/pcae/schema_runtime/manifest.py
- tests/test_cltr_cutover_136h_shared_core.py
- tests/test_cltr_cutover_136i_shared_core_independent_verification.py
- tests/test_cltr_cutover_136j_authority_core.py
- tests/test_cltr_cutover_136k_authority_core_independent_verification.py
- tests/test_cltr_cutover_136l_request_and_readiness.py
- tests/test_cltr_cutover_136m_request_and_readiness_independent_verification.py
- tests/test_cltr_cutover_136n_authorization_and_candidate.py
- tests/test_cltr_cutover_136o_authorization_and_candidate_independent_verification.py
- tests/test_schema_runtime_boundaries.py
- tests/test_schema_runtime_packaging.py
- docs/PHASE_136_AUTHORIZATION_AND_CANDIDATE_SCHEMA_INDEPENDENT_VERIFICATION.md
- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json

## Forbidden Files

- src/pcae/schema_resources/cltr_cutover/records/publication_attempt.schema.json
- src/pcae/schema_resources/cltr_cutover/records/publication_evidence.schema.json
- src/pcae/schema_resources/cltr_cutover/records/concurrency_conflict.schema.json
- src/pcae/schema_resources/cltr_cutover/bindings/**
- src/pcae/schema_resources/cltr_cutover/views/**
- .pcae/cltr-authority/**


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

- HumanAuthorization, CutoverCandidate, Certification independently re-verified against primary contract sources, not 136N's own tests/docs
- Dependency/identity/digest graphs re-derived and proven non-circular
- Zero unresolved Blocking findings, or phase explicitly reports NOT VERIFIED
- No Group 5+ schema, typed model, semantic validator, authority resolver, or authority pointer introduced

## Acceptance Checks

- python -m pytest tests/test_cltr_cutover_136o_authorization_and_candidate_independent_verification.py -q
- python -m pytest -m fast_green -n auto

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-16T21:51:23.893576+02:00
