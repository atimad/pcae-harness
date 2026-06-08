# Task Contract

## Task ID

20260608-0826-62h-runtime-rollback-boundaries

## Title

62H: Runtime Rollback Boundaries

## Status

active

## Mode

implementation

## Goal

62H: Runtime Rollback Boundaries

## Allowed Files

- .pcae/session.json
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- docs/COMMANDS.md
- src/pcae/cli.py
- src/pcae/commands/agent.py
- src/pcae/core/agent.py
- tests/test_agent.py

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

- No runtime invocation
- No prompt execution
- No source behavior changes outside task/session/handoff governance
- No execution authorization
- No commit
- No push
- No rollback

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-08T08:26:01.386937+02:00
