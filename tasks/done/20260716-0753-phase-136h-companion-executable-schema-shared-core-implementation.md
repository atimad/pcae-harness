# Task Contract

## Task ID

20260716-0753-phase-136h-companion-executable-schema-shared-core-implementation

## Title

Phase 136H: Companion Executable Schema Shared Core Implementation

## Status

done

## Mode

implementation

## Goal

Implement the Stage 3 Companion Executable Schema shared core (Group 1 per CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001): shared/ (envelope, enums, identity, digest, references, failures, limitations), deterministic manifest, minimal registry integration, and the carried-forward PREREQUISITE-136G-1 Mapping-contract repair in validate_record_shape. No authority-bearing record schema, typed model, semantic validator, or authority resolver/state/pointer.

## Allowed Files

- src/pcae/schema_resources/**
- src/pcae/schema_runtime/**
- tests/fixtures/cltr_cutover/**
- tests/fixtures/schema_runtime_136h/**
- tests/test_schema_runtime_*.py
- tests/test_cltr_cutover_*.py
- docs/PHASE_136_COMPANION_EXECUTABLE_SCHEMA_SHARED_CORE_IMPLEMENTATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/**
- tasks/done/**
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- src/pcae/cltr/**
- schemas/**
- .pcae/cltr-authority/**


## Allowed Zones

- schema_runtime
- package
- tests
- docs
- tasks
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

- Exact Group 1 shared-core inventory frozen and traceable before schema authoring
- 7 shared schema files under src/pcae/schema_resources/cltr_cutover/shared/, Draft 2020-12, unique offline-resolved $id, meta-schema valid
- Deterministic shared-core manifest with SHA-256 file digests, verified by registry integration reusing schema_runtime
- PREREQUISITE-136G-1 Mapping-contract hardening in validate_record_shape: rejects hostile Mapping, non-string keys, cyclic structures, unsupported types; preserves existing depth guard and no-mutation contract
- No authority-bearing record schema, typed model, semantic validator, or authority resolver/state/pointer created
- Fast Green and schema_runtime suite pass with zero regressions

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -m fast_green -n auto passes
- python -m pytest tests/test_schema_runtime_*.py -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-16T07:53:19.802527+02:00
