# Task Contract

## Task ID

20260618-2119-70o-acceptance-check-enforcement

## Title

70O Acceptance Check Enforcement

## Status

done

## Mode

implementation

## Goal

Make pcae task finish enforce the acceptance checks declared in the active task contract.

## Allowed Files

- src/pcae/core/tasks.py
- src/pcae/commands/task.py
- src/pcae/cli.py
- tests/test_task.py
- docs/COMMANDS.md
- CHANGELOG.md
- PROJECT_STATUS.md
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

- task finish executes declared acceptance checks
- task finish refuses when acceptance check fails
- task finish --commit refuses before commit on check failure
- task finish --skip-checks bypasses acceptance checks
- task finish --json includes acceptance check results
- task complete remains backward compatible
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-18T21:19:15.091238+02:00
