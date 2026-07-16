# Task Contract

## Task ID

20260716-1842-phase-136m-request-and-readiness-schema-independent-verification

## Title

Phase 136M: Request and Readiness Schema Independent Verification

## Status

active

## Mode

implementation

## Goal

Independently verify and adversarially attack the CutoverRequest and ReadinessPackage Group 3 executable schemas from Phase 136L; repair genuine bounded defects; produce the canonical 136M independent-verification document.

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- src/pcae/schema_resources/cltr_cutover/records/cutover_request.schema.json
- src/pcae/schema_resources/cltr_cutover/records/readiness_package.schema.json
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
- tests/test_schema_runtime_boundaries.py
- tests/test_schema_runtime_packaging.py
- docs/PHASE_136_REQUEST_AND_READINESS_SCHEMA_INDEPENDENT_VERIFICATION.md
- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json

## Forbidden Files

- src/pcae/schema_resources/cltr_cutover/records/human_authorization.schema.json
- src/pcae/schema_resources/cltr_cutover/records/cutover_candidate.schema.json
- src/pcae/schema_resources/cltr_cutover/records/certification.schema.json
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

- CutoverRequest and ReadinessPackage independently re-verified against primary contract sources, not 136L's own tests/docs
- Creation order re-derived and proven non-circular via fresh  and identity/digest dependency graphs
- Zero unresolved Blocking findings, or phase explicitly reports NOT VERIFIED
- No Group 4+ schema, typed model, semantic validator, authority resolver, or authority pointer introduced

## Acceptance Checks

- python -m pytest tests/test_cltr_cutover_136m_request_and_readiness_independent_verification.py -q
- python -m pytest -m fast_green -n auto

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-16T18:42:24.579711+02:00
