# Task Contract

## Task ID

20260618-0605-70h-governed-push-execution

## Title

70H Governed Push Execution

## Status

active

## Mode

implementation

## Goal

Add pcae push as a governed command that runs push check internally then executes git push only if the check passes.

## Allowed Files

- src/pcae/cli.py
- src/pcae/commands/push.py
- tests/test_push.py
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

- pcae push validates then pushes in one command
- pcae push refuses when check would refuse
- pcae push --dry-run never pushes
- pcae push --json includes push metadata
- pcae push check behavior unchanged
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-18T06:05:09.327913+02:00
