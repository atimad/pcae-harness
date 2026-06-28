# Task Contract

## Task ID

20260628-1252-89d-dry-run-blocking-simulation-test-matrix-and-cli-stability-review

## Title

89D — Dry-Run Blocking Simulation Test Matrix and CLI Stability Review

## Status

active

## Mode

implementation

## Goal

Expand dry-run blocking simulation test matrix and review CLI stability across check/explain/status, JSON/human-readable output, hard-block/redaction preservation, and all safety invariants.

## Allowed Files

- tests/test_dry_run_simulation.py
- tests/test_dry_run_cli.py
- src/pcae/core/dry_run.py
- src/pcae/commands/dry_run.py
- docs/PHASE_89_DRY_RUN_BLOCKING_SIMULATION_TEST_MATRIX.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**
- tasks/done/**

## Forbidden Files

- src/pcae/core/shell_gate.py
- src/pcae/core/permission_broker.py
- src/pcae/core/advisory.py
- src/pcae/commands/advisory.py
- src/pcae/core/gate_dry_run.py
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

advisory

## Forbidden Changes

- TBD

## Acceptance Criteria

- Test matrix expanded across all 8 categories
- CLI stability reviewed
- All safety invariants verified
- All test tiers pass

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-28T12:52:23.189720+02:00
