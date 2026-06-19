# Task Contract

## Task ID

20260619-1305-phase-71m-phase-prompt-visibility-in-bootstrap-and-handoff

## Title

Phase 71M phase prompt visibility in bootstrap and handoff

## Status

done

## Mode

implementation

## Goal

Surface latest captured phase prompt metadata in handoff artifacts, handoff-show, compact bootstrap, and continuity-check.

## Allowed Files

- src/pcae/commands/phase.py
- src/pcae/commands/session.py
- src/pcae/core/context.py
- src/pcae/core/session.py
- tests/test_phase.py
- tests/test_session.py
- CHANGELOG.md
- PROJECT_STATUS.md
- tasks/**

## Forbidden Files

- src/pcae/commands/push.py

## Allowed Zones

- commands
- core
- tests
- tasks
- docs

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

advisory

## Forbidden Changes

- No prompt execution
- No mutation during prompt visibility reads

## Acceptance Criteria

- Handoff artifact includes latest prompt metadata when a captured prompt exists
- pcae phase handoff-show --json includes prompt visibility fields
- Compact bootstrap shows concise latest prompt metadata when prompt exists
- pcae session continuity-check --json includes prompt presence/title/path
- Tests cover prompt present/absent in handoff, bootstrap, and continuity-check

## Acceptance Checks

- python -m pytest tests/test_phase.py tests/test_session.py
- python -m pytest -n auto
- pcae health
- pcae check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-19T13:05:25.863166+02:00
