# Task Contract

## Task ID

20260919-1140-n16-5-f-5-tb-fast-green-stale-assertion-repair-repair-two-current-head-bound-stale-assertions-in-fast-green-baseline-freeze-evidence-repair-tests

## Title

N16-5-F-5-TB-FAST-GREEN-STALE-ASSERTION-REPAIR: repair two current-HEAD-bound stale assertions in fast-green baseline-freeze evidence-repair tests

## Status

active

## Mode

implementation

## Goal

Repair test_no_production_source_changed_in_this_phase and test_stale_assumption_fails_against_modern_head_for_a_legitimate_reason in tests/test_n16_5_f_5_tb_fast_green_baseline_freeze_evidence_repair.py, which incorrectly bind historical phase-local claims to 'HEAD' instead of the phase's own pinned final commit, causing false Fast Green failures on any later legitimate src/pcae/** edit. Preserve original security intent and mutation sensitivity. Test/evidence-only phase; zero src/pcae or contract changes. N-16-5 remains OPEN.

## Allowed Files

- tests/**
- docs/**
- tasks/**
- .pcae/**
- PROJECT_STATUS.md
- CHANGELOG.md

## Forbidden Files

- src/pcae/**
- docs/contracts/**


## Allowed Zones

- tests
- docs
- tasks
- config

## Forbidden Zones

- core

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

2026-09-19T11:40:29.642891+02:00
