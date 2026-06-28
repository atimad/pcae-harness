# Task Contract

## Task ID

20260628-1217-89c-dry-run-blocking-simulation-prototype

## Title

89C — Dry-Run Blocking Simulation Prototype

## Status

done

## Mode

implementation

## Goal

Implement the first read-only dry-run blocking simulation prototype: pcae dry-run check/explain/status commands that evaluate commands through advisory/broker/shell-gate logic without executing, intercepting, or authorizing anything.

## Allowed Files

- src/pcae/core/dry_run.py
- src/pcae/commands/dry_run.py
- src/pcae/cli.py
- tests/test_dry_run_simulation.py
- tests/test_dry_run_cli.py
- docs/PHASE_89_DRY_RUN_BLOCKING_SIMULATION_PROTOTYPE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**
- tasks/done/**

## Forbidden Files

- src/pcae/core/gate_dry_run.py
- src/pcae/core/gate_dry_run_context.py
- src/pcae/core/project_state.py
- src/pcae/core/shell_gate.py
- src/pcae/core/permission_broker.py
- src/pcae/core/advisory.py
- src/pcae/commands/advisory.py
- .githooks/**
- docs/LINKEDIN_ARTICLE_DRAFT.md
- docs/REAL_CAPTURED_TASKS.md


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

- Dry-run simulation core module implemented
- Dry-run CLI commands registered
- pcae dry-run check/explain/status work with --json
- All safety invariants present
- Focused tests pass
- All test tiers pass

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-28T12:17:19.481970+02:00
