# Task Contract

## Task ID

20260922-2052-phase-150g-n16-5-f-5-tb-helper-admission-recognition-core-implementation-extract-pawa-recognition-steps-1-8-into-shared-core-module

## Title

Phase 150G (N16-5-F-5-TB-HELPER-ADMISSION-RECOGNITION-CORE-IMPLEMENTATION): Extract PAWA recognition steps 1-8 into shared core module

## Status

done

## Mode

implementation

## Goal

Implement Model B from Phase 150F: extract hpac_protected_admin_writer._run_recognition_sequence steps 1-8 into a new neutral, non-agent-importable module (hpac_pawa_recognition_core.py), refactor the legacy factory to call it (behavior-preserving), with fresh tests proving parity and non-authoritative result semantics. No helper wiring, no step 9-prime, no foundation repair, no contract changes.

## Allowed Files

- src/pcae/core/**
- tests/**
- docs/**
- tasks/**
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/**

## Forbidden Files

- TBD


## Allowed Zones

- core
- tests
- docs
- tasks
- config

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

- New hpac_pawa_recognition_core.py implements steps 1-8 read-only, no writer/helper authority, no mutation, importable by legacy factory
- hpac_protected_admin_writer.py refactored to call the shared core; no duplicate step 1-8 logic remains
- Behavior parity: old vs new fail-closed outcomes identical for all recognition failure paths
- Helper admission modules untouched; step 9-prime not defined; Model E unchanged; foundation boundary untouched; zero docs/contracts changes
- Fast Green attributable_failures: []

## Acceptance Checks

- python -m pytest tests/test_n16_5_f_5_tb_helper_admission_recognition_core_implementation.py -q

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-22T20:52:05.827155+02:00
