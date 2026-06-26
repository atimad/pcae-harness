# Task Contract

## Task ID

20260626-0814-phase-88n-5-fast-green-validation-architecture

## Title

Phase 88N.5 — Fast Green Validation Architecture

## Status

active

## Mode

implementation

## Goal

Define a fast-green validation tier (1-2 minute target, high-signal governance tests) as a practical normal development gate. Adds pytest marker fast_green via conftest.py auto-marker, declares it in pyproject.toml, creates tests/test_88n5_fast_green_validation.py, documents in docs/PHASE_88_FAST_GREEN_VALIDATION_ARCHITECTURE.md. No source changes, no test weakening, no skip/xfail for speed.

## Allowed Files

- tests/conftest.py
- tests/test_88n5_fast_green_validation.py
- pyproject.toml
- docs/PHASE_88_FAST_GREEN_VALIDATION_ARCHITECTURE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**
- tasks/DONE.md

## Override Protected Files

- pyproject.toml

## Forbidden Files

- src/**
- .githooks/**


## Allowed Zones

- TBD

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

TBD

## Forbidden Changes

- TBD

## Acceptance Criteria

- TBD

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-26T08:14:13.755285+02:00
