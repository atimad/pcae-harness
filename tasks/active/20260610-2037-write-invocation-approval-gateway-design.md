# Task Contract

## Task ID

20260610-2037-write-invocation-approval-gateway-design

## Title

Write Invocation Approval Gateway Design

## Status

active

## Mode

implementation

## Goal

Write Invocation Approval Gateway Design

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
- tests/test_agent.py
- docs/COMMANDS.md
- docs/CAPABILITY_INVENTORY.md

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

2026-06-10T20:37:18.463004+02:00
