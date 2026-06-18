# Task Contract

## Task ID

20260618-0024-70c-session-continuity-deduplication

## Title

70C Session Continuity Deduplication

## Status

active

## Mode

implementation

## Goal

Deduplicate the 4 copies of session_continuity_status into a single canonical function. All call sites in health.py, export.py, architecture.py, and commands/check.py should import from one location.

## Allowed Files

- src/pcae/core/session.py
- src/pcae/core/health.py
- src/pcae/core/export.py
- src/pcae/core/architecture.py
- src/pcae/core/check.py
- src/pcae/commands/check.py
- tests/test_session.py
- tests/test_health.py
- tests/test_check.py
- tests/test_export.py
- tests/test_architecture.py
- tasks/active/**
- PROJECT_STATUS.md

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

- Only one definition of session_continuity_status exists
- All 4 former call sites import from the canonical location
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-18T00:24:56.773610+02:00
