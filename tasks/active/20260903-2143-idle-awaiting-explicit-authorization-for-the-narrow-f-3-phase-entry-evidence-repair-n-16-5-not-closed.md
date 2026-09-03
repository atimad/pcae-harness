# Task Contract

## Task ID

20260903-2143-idle-awaiting-explicit-authorization-for-the-narrow-f-3-phase-entry-evidence-repair-n-16-5-not-closed

## Title

Idle: awaiting explicit authorization for the narrow F-3 phase-entry evidence repair; N-16-5 NOT CLOSED

## Status

active

## Mode

implementation

## Goal

Idle: awaiting explicit authorization for the narrow F-3 phase-entry evidence repair; N-16-5 NOT CLOSED

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

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

- No runtime invocation
- No prompt execution
- No source behavior changes outside task/session/handoff governance
- No execution authorization
- No commit except governed `.30R.5R.2.1` completion finalization
- No push except governed `.30R.5R.2.1` completion finalization
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

2026-09-03T21:43:26.512118+02:00
