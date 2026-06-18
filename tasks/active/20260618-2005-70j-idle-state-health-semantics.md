# Task Contract

## Task ID

20260618-2005-70j-idle-state-health-semantics

## Title

70J Idle State Health Semantics

## Status

active

## Mode

implementation

## Goal

Teach PCAE to distinguish healthy idle from unsafe no-active-task drift.

## Allowed Files

- src/pcae/core/health.py
- src/pcae/core/check.py
- src/pcae/commands/check.py
- src/pcae/commands/health.py
- src/pcae/commands/push.py
- src/pcae/cli.py
- tests/test_health.py
- tests/test_check.py
- tests/test_push.py
- tests/test_session.py
- tests/test_phase.py
- tests/test_orchestration.py
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**

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

- pcae health reports healthy idle when clean no-task state
- pcae health reports unhealthy when no task and dirty tree
- pcae check exits 0 when no task and clean tree
- pcae check exits 1 when no task and dirty tree
- pcae check enforces scope when active task exists
- pcae push check reports nothing_to_push for healthy idle
- post_finish_closure mode preserved
- active-task behavior unchanged
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-18T20:05:25.983235+02:00
