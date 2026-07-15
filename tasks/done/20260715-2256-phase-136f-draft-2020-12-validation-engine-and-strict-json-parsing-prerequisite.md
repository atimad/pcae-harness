# Task Contract

## Task ID

20260715-2256-phase-136f-draft-2020-12-validation-engine-and-strict-json-parsing-prerequisite

## Title

Phase 136F: Draft 2020-12 Validation Engine and Strict JSON Parsing Prerequisite

## Status

done

## Mode

implementation

## Goal

Implement and independently verify only the prerequisite infrastructure required before Stage 3 executable companion-schema authoring begins: jsonschema Draft 2020-12 validation engine, strict duplicate-key-safe JSON parsing, offline-only schema loading/registry foundation, deterministic schema-package discovery, packaging resolution for future schema files (PREREQUISITE-136E-1), minimal shape-validation result/error model, and proof the infrastructure cannot resolve authority or mutate production state. No Stage 3 record schemas, typed models, semantic validation, or authority resolution.

## Allowed Files

- pyproject.toml
- src/pcae/schema_runtime/**
- src/pcae/schema_resources/**
- tests/fixtures/schema_runtime/**
- tests/test_schema_runtime_*.py
- tests/conftest.py
- docs/PHASE_136_DRAFT_2020_12_VALIDATION_ENGINE_AND_STRICT_JSON_PARSING_PREREQUISITE.md
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

## Override Protected Files

- pyproject.toml

## Acceptance Criteria

- jsonschema>=4.18,<5 declared as a dependency and proven to support Draft 2020-12
- Strict duplicate-key-rejecting, non-finite-number-rejecting JSON parser implemented with focused tests
- Offline-only schema resource loader and registry foundation implemented with no-network and containment proofs
- Packaging resolved so a schema resource package is included in editable install, wheel, and sdist
- No Stage 3 record schema, typed model, semantic validator, authority resolver, or authority state created
- Fast Green passes with zero regressions

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-15T22:56:51.146506+02:00
