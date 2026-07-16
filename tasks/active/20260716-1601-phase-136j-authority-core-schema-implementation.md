# Task Contract

## Task ID

20260716-1601-phase-136j-authority-core-schema-implementation

## Title

Phase 136J: Authority Core Schema Implementation

## Status

active

## Mode

implementation

## Goal

Phase 136J: Authority Core Schema Implementation

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- src/pcae/schema_resources/__init__.py
- src/pcae/schema_resources/cltr_cutover/README.md
- src/pcae/schema_resources/cltr_cutover/manifest.json
- src/pcae/schema_resources/cltr_cutover/records/*
- src/pcae/schema_resources/cltr_cutover/records/**
- tests/test_cltr_cutover_136h_shared_core.py
- tests/test_cltr_cutover_136i_shared_core_independent_verification.py
- tests/test_schema_runtime_boundaries.py
- tests/test_schema_runtime_packaging.py
- tests/test_cltr_cutover_136j_authority_core.py
- docs/PHASE_136_AUTHORITY_CORE_SCHEMA_IMPLEMENTATION.md
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

- No runtime invocation
- No prompt execution
- No source behavior changes outside task/session/handoff governance
- No execution authorization
- No commit
- No push
- No rollback

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

2026-07-16T16:01:41.100853+02:00
