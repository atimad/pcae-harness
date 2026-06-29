# Task Contract

## Task ID

20260629-2131-phase-94w-real-adapter-preflight-hardening

## Title

Phase 94W — Real Adapter Preflight Hardening

## Status

done

## Mode

implementation

## Goal

Phase 94W — Real Adapter Preflight Hardening

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- src/pcae/core/backend_invocations.py
- tests/test_backend_invocations.py
- docs/PHASE_94_REAL_ADAPTER_PREFLIGHT_HARDENING.md

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

2026-06-29T21:31:09.610242+02:00
