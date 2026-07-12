# Task Contract

## Task ID

20260712-1041-correct-phase-134e-10-1-1-planned-completed-trailing-letter-regex-collision

## Title

Correct Phase 134E.10.1.1 planned/completed trailing-letter regex collision

## Status

active

## Mode

governance

## Goal

Fix _leading_phase_id/_parenthetical_phase_id regexes in validate_derived_correctness (phase_reports.py) to preserve a trailing letter after the last dot-digit group, avoiding a false 'planned phase is also completed' collision (134E.10.1V misparsed as 134E.10.1, which is genuinely completed) that blocked this phase's own governed finalization.

## Allowed Files

- src/pcae/core/phase_reports.py
- tasks/active/20260712-1041-correct-phase-134e-10-1-1-planned-completed-trailing-letter-regex-collision.md

## Forbidden Files

- TBD


## Allowed Zones

- core
- tasks
- docs

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

TBD

## Forbidden Changes

- TBD

## Acceptance Criteria

- TBD

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-12T10:41:03.671251+02:00
