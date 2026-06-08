# Task Contract

## Task ID

20260608-1220-63a-multi-runtime-registry

## Title

63A: Multi-Runtime Registry

## Status

active

## Mode

implementation

## Goal

63A: Multi-Runtime Registry

## Allowed Files

- .pcae/session.json
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- src/pcae/core/agent.py
- src/pcae/core/docs.py
- src/pcae/commands/agent.py
- src/pcae/cli.py
- docs/COMMANDS.md
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

2026-06-08T12:20:57.807337+02:00
