# Task Contract

## Task ID

20260617-2340-70b-task-health-and-runtime-hygiene

## Title

70B Task Health and Runtime Hygiene

## Status

active

## Mode

implementation

## Goal

Implement pcae doctor task-memory for detecting task-memory inconsistencies. Untrack runtime session files and make pcae init/gitignore defaults handle them correctly.

## Allowed Files

- src/pcae/cli.py
- src/pcae/commands/check.py
- src/pcae/commands/task.py
- src/pcae/core/architecture.py
- src/pcae/core/check.py
- src/pcae/core/export.py
- src/pcae/core/health.py
- src/pcae/core/tasks.py
- src/pcae/core/templates.py
- .pcae/.gitignore
- .pcae/session.json
- docs/COMMANDS.md
- CHANGELOG.md
- PROJECT_STATUS.md
- tasks/active/**
- tasks/done/**
- tests/test_task.py
- tests/test_check.py
- tests/test_agent.py
- tests/test_export.py
- tests/test_health.py
- tests/test_session.py
- tests/test_architecture.py

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

- TBD

## Acceptance Checks

- pcae doctor task-memory detects all 6 inconsistency types
- pcae doctor task-memory --json emits structured output
- .pcae/session.json is untracked after this phase
- pcae init generates correct .pcae/.gitignore defaults
- pcae check no longer flags session.json as out-of-scope
- pcae health does not fail when session.json is gitignored
- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-17T23:40:14.908216+02:00
