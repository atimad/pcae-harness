# Task Contract

## Task ID

20260619-1222-phase-71j-post-clear-continuity-validation

## Title

Phase 71J post-clear continuity validation

## Status

done

## Mode

implementation

## Goal

Add a read-only continuity validation command (pcae session continuity-check) that validates repo state for post-clear/session-reset continuation.

## Allowed Files

- src/pcae/cli.py
- src/pcae/commands/session.py
- src/pcae/core/session.py
- tests/test_session.py
- CHANGELOG.md
- PROJECT_STATUS.md
- tasks/**

## Forbidden Files

- src/pcae/commands/push.py
- src/pcae/core/phase.py

## Allowed Zones

- commands
- core
- tests
- cli
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

- No mutation during continuity-check
- No task finish changes
- No push changes
- No phase queue execution

## Acceptance Criteria

- pcae session continuity-check produces human-readable continuity report
- pcae session continuity-check --json produces structured output
- Command is read-only
- Reports handoff artifact presence/status
- Reports audit artifact presence/status
- Reports phase queue presence/count
- Reports active/idle task state
- Reports whether repo is suitable for continuation
- Tests cover healthy continuity, missing handoff, missing audit, non-empty queue, and dirty tree

## Acceptance Checks

- python -m pytest tests/test_session.py
- python -m pytest -n auto
- pcae health
- pcae check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-19T12:22:11.597107+02:00
