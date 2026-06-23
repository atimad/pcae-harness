# Task Contract

## Task ID

20260623-0856-phase-82d-subagent-safety-profile

## Title

Phase 82D Subagent Safety Profile

## Status

done

## Mode

documentation

## Goal

Design the subagent safety profile model: risk classes, permission boundaries, approval requirements, mutation handling, output intake, and forbidden behaviors. Design only, no probing or execution.

## Allowed Files

- docs/SUBAGENT_SAFETY_PROFILE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active
- tasks/active/*

## Forbidden Files

- docs/REAL_CAPTURED_TASKS.md
- src/**
- tests/**

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
- Source code modification
- Test modification
- Backend invocation
- Subagent probing

## Acceptance Criteria

- Safety profile artifact exists
- Defines risk levels, permission boundaries, approval model
- No backend invocation or subagent probing

## Acceptance Checks

- pcae health
- pcae check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-23T08:56:08.511327+02:00
