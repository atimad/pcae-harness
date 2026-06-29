# Task Contract

## Task ID

20260629-2058-phase-94t-real-backend-adapter-preflight-cli

## Title

Phase 94T — Real Backend Adapter Preflight CLI

## Status

active

## Mode

implementation

## Goal

Phase 94T — Real Backend Adapter Preflight CLI

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- src/pcae/cli.py
- src/pcae/commands/backend.py
- tests/test_backend_cli.py
- docs/PHASE_94_BACKEND_REAL_ADAPTER_PREFLIGHT_CLI.md

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

2026-06-29T20:58:38.224005+02:00
