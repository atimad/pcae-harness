# Task Contract

## Task ID

20260619-1239-phase-71k-phase-prompt-capture

## Title

Phase 71K phase prompt capture

## Status

done

## Mode

implementation

## Goal

Add local phase prompt capture command to save human-provided phase prompts as local runtime artifacts before execution.

## Allowed Files

- .pcae/.gitignore
- src/pcae/cli.py
- src/pcae/commands/phase.py
- src/pcae/core/templates.py
- tests/test_phase.py
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
- config

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
- No automatic task creation from captured prompt
- No phase queue execution
- No task finish changes
- No push changes

## Acceptance Criteria

- phase prompt capture can save text from --text
- phase prompt capture can save text from --file
- phase prompt capture can save text from stdin
- latest.md is updated
- timestamped prompt artifact is created
- generated prompt artifacts are ignored by git
- --json output includes prompt path, title, created_at, and latest path
- command is capture-only

## Acceptance Checks

- python -m pytest tests/test_phase.py
- python -m pytest -n auto
- pcae health
- pcae check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-19T12:39:14.489600+02:00
