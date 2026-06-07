# Task Contract

## Task ID

20260607-1400-61h-automated-task-transition

## Title

Automated Task Transition (Phase 61H)

## Status

done

## Mode

implementation

## Goal

Implement `pcae task transition`, `pcae task transition --next`, and `pcae task transition --json` so PCAE can safely complete the current governed task, create the next active task, refresh session continuity, and update governance memory files in Phase 61H.

## Allowed Files

- .pcae/session.json
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- CHANGELOG.md
- PROJECT_STATUS.md
- docs/COMMANDS.md
- src/pcae/cli.py
- src/pcae/commands/check.py
- src/pcae/commands/health.py
- src/pcae/commands/status.py
- src/pcae/commands/task.py
- src/pcae/core/check.py
- src/pcae/core/docs.py
- src/pcae/core/session.py
- src/pcae/core/status.py
- src/pcae/core/tasks.py
- tests/test_docs.py
- tests/test_task.py

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

- pcae task transition works
- pcae task transition --next works
- pcae task transition --json works
- stale active task is prevented
- session is refreshed
- next task is created with valid scope
- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-07T14:00:00.000000+02:00
