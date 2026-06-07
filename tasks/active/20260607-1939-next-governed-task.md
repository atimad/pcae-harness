# Task Contract

## Task ID

20260607-1939-next-governed-task

## Title

Next governed task

## Status

active

## Mode

implementation

## Goal

Next governed task

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
- src/pcae/commands/task.py
- src/pcae/core/agent.py
- src/pcae/core/context.py
- src/pcae/core/docs.py
- src/pcae/core/tasks.py
- pyproject.toml
- tests/test_agent.py
- tests/test_context.py
- tests/test_task.py

## Override Protected Files

- pyproject.toml

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

2026-06-07T19:39:38.896567+02:00
