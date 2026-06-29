# Task Contract

## Task ID

20260629-2107-phase-94t-1-phase-completion-metadata-freshness-guard

## Title

Phase 94T.1 — Phase Completion Metadata Freshness Guard

## Status

active

## Mode

implementation

## Goal

Phase 94T.1 — Phase Completion Metadata Freshness Guard

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- src/pcae/commands/phase.py
- src/pcae/core/phase_reports.py
- tests/test_phase_reports.py
- docs/PHASE_94T1_PHASE_COMPLETION_METADATA_FRESHNESS_GUARD.md

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

2026-06-29T21:07:18.921327+02:00
