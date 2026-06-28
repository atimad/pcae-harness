# Task Contract

## Task ID

20260628-1408-89e-dry-run-blocking-simulation-ux-refinement-and-operator-guidance

## Title

89E — Dry-Run Blocking Simulation UX Refinement and Operator Guidance

## Status

active

## Mode

implementation

## Goal

Refine dry-run simulation human-readable output and operator guidance: blocked, allowed, review-required, and unknown decisions clearer; hard-block wording stronger; simulation-only footer preserved.

## Allowed Files

- src/pcae/commands/dry_run.py
- src/pcae/core/dry_run.py
- tests/test_dry_run_simulation.py
- tests/test_dry_run_cli.py
- docs/PHASE_89_DRY_RUN_BLOCKING_SIMULATION_UX_REFINEMENT.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**
- tasks/done/**

## Forbidden Files

- src/pcae/core/shell_gate.py
- src/pcae/core/advisory.py
- src/pcae/core/permission_broker.py
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

- Human-readable output refined for all 4 decision categories
- Hard-block wording non-overridable
- JSON schema and safety invariants preserved
- All test tiers pass

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-28T14:08:28.209925+02:00
