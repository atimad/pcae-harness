# Task Contract

## Task ID

20260629-2244-phase-95a-artifact-only-real-invocation-dry-run-boundary

## Title

Phase 95A — Artifact-Only Real Invocation Dry-Run Boundary

## Status

active

## Mode

implementation

## Goal

Phase 95A — Artifact-Only Real Invocation Dry-Run Boundary

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/.gitignore
- src/pcae/cli.py
- src/pcae/commands/backend.py
- src/pcae/core/backend_invocations.py
- tests/test_backend_invocations.py
- docs/PHASE_95_ARTIFACT_ONLY_REAL_INVOCATION_DRY_RUN_BOUNDARY.md

## Forbidden Files

- TBD

## Override Protected Files

- pyproject.toml


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

2026-06-29T22:44:45.928667+02:00
