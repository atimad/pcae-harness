# Task Contract

## Task ID

20260720-0705-phase-137i-1-finalization-ordering-deadlock-repair

## Title

Phase 137I.1 — Finalization Ordering Deadlock Repair

## Status

active

## Mode

implementation

## Goal

Repair the finalization-ordering deadlock in which a completed-but-unpushed phase cannot be finalized through governed PCAE workflows because push readiness depends on a canonical report that governed finalization refuses to write until pushed. Add a governed pending-report escape and case-insensitive phase-identity consistency; preserve all trust guarantees.

## Allowed Files

- src/pcae/core/phase_reports.py
- src/pcae/core/repository_transition_validator.py
- src/pcae/commands/phase.py
- src/pcae/cli.py
- tests/**
- docs/**
- tasks/**
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json

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

strict

## Forbidden Changes

- TBD

## Acceptance Criteria

- TBD

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-20T07:05:32.980823+02:00
