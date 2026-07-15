# Task Contract

## Task ID

20260716-0036-phase-136g-validation-engine-and-strict-json-parsing-independent-verification

## Title

Phase 136G: Validation Engine and Strict JSON Parsing Independent Verification

## Status

active

## Mode

implementation

## Goal

Independently verify and adversarially attack the generic Draft 2020-12 validation-engine, strict-parser, registry, loader, packaging, containment, and no-authority/no-execution infrastructure introduced by Phase 136F. Add independent adversarial tests; repair only genuine defects within the generic schema-runtime boundary; produce a canonical independent-verification report and definitive verdict. No Stage 3 schema authoring.

## Allowed Files

- src/pcae/schema_runtime/**
- src/pcae/schema_runtime/*.py
- src/pcae/schema_resources/**
- tests/fixtures/schema_runtime/**
- tests/fixtures/schema_runtime_136g/**
- tests/fixtures/schema_runtime_136g
- tests/test_schema_runtime_*.py
- tests/test_schema_runtime_136g_independent_verification.py
- tests/conftest.py
- pyproject.toml
- docs/PHASE_136_VALIDATION_ENGINE_AND_STRICT_JSON_PARSING_INDEPENDENT_VERIFICATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/**
- tasks/done/**
- .pcae/policy.toml
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- schemas/cltr_cutover/**
- src/pcae/cltr/**


## Allowed Zones

- schema_runtime
- package
- tests
- docs
- tasks
- policy
- config

## Forbidden Zones

- cltr

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

strict

## Forbidden Changes

- TBD

## Acceptance Criteria

- Independently re-derive and adversarially attack Draft 2020-12 conformance, strict-parser behavior, resource limits, loader containment, registry no-network/determinism, shape-validation API, error vocabulary, packaging, no-authority, no-execution, filesystem non-mutation
- Repair only genuine defects found, within the generic schema-runtime boundary; add regression tests
- Produce docs/PHASE_136_VALIDATION_ENGINE_AND_STRICT_JSON_PARSING_INDEPENDENT_VERIFICATION.md with a definitive verdict
- No Stage 3 schema, fixture, typed model, semantic validator, or authority resolver/state/pointer created
- Fast Green passes with zero regressions

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-16T00:36:46.906696+02:00
