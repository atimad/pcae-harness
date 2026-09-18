# Task Contract

## Task ID

20260918-2223-n16-5-f-5-tb-fast-green-baseline-freeze-evidence-repair-repair-stale-full-tree-src-pcae-hash-freeze-test-blocking-fast-green

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1 (N16-5-F-5-TB-FAST-GREEN-BASELINE-FREEZE-EVIDENCE-REPAIR): repair stale full-tree src/pcae hash-freeze test blocking Fast Green

## Status

active

## Mode

implementation

## Goal

Identify and repair the stale historical full-tree src/pcae/** hash-freeze test (test_all_production_sources_remain_byte_identical_to_recorded_baseline) that blocks Fast Green for any future legitimate src/pcae edit; preserve its original historical security claim as a commit-scoped historical assertion; add fresh adversarial tests; restore clean Fast Green attribution. Test/evidence-only phase; zero src/pcae or contract changes. N-16-5 remains OPEN.

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

2026-09-18T22:23:33.342169+02:00
