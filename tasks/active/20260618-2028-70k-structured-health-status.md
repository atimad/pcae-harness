# Task Contract

## Task ID

20260618-2028-70k-structured-health-status

## Title

70K Structured Health Status

## Status

active

## Mode

implementation

## Goal

Replace string-based health gating with explicit structured health status values while preserving user-facing output.

## Allowed Files

- src/pcae/core/health.py
- src/pcae/core/check.py
- src/pcae/core/fleet.py
- src/pcae/core/orchestration.py
- src/pcae/core/phase.py
- src/pcae/core/pipeline.py
- src/pcae/core/tasks.py
- src/pcae/commands/health.py
- src/pcae/commands/push.py
- src/pcae/cli.py
- tests/test_health.py
- tests/test_push.py
- tests/test_check.py
- tests/test_orchestration.py
- tests/test_phase.py
- tests/test_pipeline.py
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**
- tasks/TODO.md

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

advisory

## Forbidden Changes

- TBD

## Acceptance Checks

- health status has structured internal representation
- callers use structured status instead of startswith
- pcae health output remains user-compatible
- pcae push check handles all modes correctly
- tests prove no startswith health gating remains
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-18T20:28:44.843674+02:00
