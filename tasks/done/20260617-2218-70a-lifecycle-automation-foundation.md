# Task Contract

## Task ID

20260617-2218-70a-lifecycle-automation-foundation

## Title

70A Lifecycle Automation Foundation

## Status

done

## Mode

implementation

## Goal

Implement pcae task finish as a governed task-closure command that validates acceptance checks, moves the active task to done, updates task memory files, refreshes session state, and emits structured output.

## Allowed Files

- src/pcae/cli.py
- src/pcae/commands/task.py
- src/pcae/core/tasks.py
- tests/test_task.py
- docs/COMMANDS.md
- CHANGELOG.md
- .pcae/session.json

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

- pcae task finish completes exactly one active task safely
- pcae task finish refuses when required checks fail
- pcae task finish updates tasks/DONE.md
- pcae task finish refreshes .pcae/session.json
- pcae task finish emits --json structured output
- pcae task complete behavior unchanged
- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-17T22:18:39.973846+02:00
