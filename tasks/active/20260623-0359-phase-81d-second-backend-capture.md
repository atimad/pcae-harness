# Task Contract

## Task ID

20260623-0359-phase-81d-second-backend-capture

## Title

Phase 81D Second Backend Capture

## Status

active

## Mode

implementation

## Goal

Invoke locked backend claude-local exactly once with REAL-CAPTURED-TASK-002 prompt, capture output, detect mutation. Do not apply, adopt, stage, commit, or push backend output.

## Allowed Files

- docs/SECOND_BACKEND_CAPTURE_RESULT.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active
- tasks/active/*

## Forbidden Files

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

strict

## Forbidden Changes

- docs/REAL_CAPTURED_TASKS.md modification
- Backend output application
- Backend output adoption
- Backend output staging
- Backend output commit
- Backend output push

## Acceptance Criteria

- Backend invoked exactly once
- Output captured
- Mutation guard before/after recorded
- Output not applied, adopted, staged, committed, or pushed

## Acceptance Checks

- pcae health
- pcae check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-23T03:59:26.411022+02:00
