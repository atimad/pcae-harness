# Task Contract

## Task ID

20260716-1655-phase-136k-authority-core-schema-independent-verification

## Title

Phase 136K: Authority Core Schema Independent Verification

## Status

active

## Mode

implementation

## Goal

Independently verify and adversarially attack the AuthorityEpoch and AuthorityState Group 2 executable schemas from Phase 136J; repair genuine bounded defects; produce the canonical 136K independent-verification document.

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- src/pcae/schema_resources/cltr_cutover/records/*
- src/pcae/schema_resources/cltr_cutover/manifest.json
- src/pcae/schema_runtime/manifest.py
- tests/test_cltr_cutover_136h_shared_core.py
- tests/test_cltr_cutover_136i_shared_core_independent_verification.py
- tests/test_cltr_cutover_136j_authority_core.py
- tests/test_cltr_cutover_136k_authority_core_independent_verification.py
- tests/test_schema_runtime_boundaries.py
- tests/test_schema_runtime_packaging.py
- docs/PHASE_136_AUTHORITY_CORE_SCHEMA_INDEPENDENT_VERIFICATION.md
- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json

## Forbidden Files

- src/pcae/schema_resources/cltr_cutover/records/cutover_request.schema.json
- src/pcae/schema_resources/cltr_cutover/records/readiness_package.schema.json
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

- AuthorityEpoch and AuthorityState independently re-verified against primary sources, not 136J's own tests/docs
- Zero unresolved Blocking findings, or phase explicitly reports NOT VERIFIED
- No Group 3+ schema, typed model, semantic validator, authority resolver, or authority pointer introduced

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-16T16:55:45.017561+02:00
