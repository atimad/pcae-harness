# Task Contract

## Task ID

20260619-1249-phase-71l-phase-prompt-show

## Title

Phase 71L phase prompt show

## Status

done

## Mode

implementation

## Goal

Add phase prompt display/read commands: prompt-show and prompt-list.

## Allowed Files

- src/pcae/cli.py
- src/pcae/commands/phase.py
- tests/test_phase.py
- CHANGELOG.md
- PROJECT_STATUS.md
- tasks/**

## Forbidden Files

- src/pcae/commands/push.py

## Allowed Zones

- commands
- cli
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
- No automatic task creation from captured prompt
- No mutation during prompt-show/prompt-list

## Acceptance Criteria

- pcae phase prompt-show displays latest captured prompt
- pcae phase prompt-show --json outputs structured metadata and content
- pcae phase prompt-list lists captured prompts
- Missing prompt artifact returns clear error and nonzero exit
- show/list are read-only

## Acceptance Checks

- python -m pytest tests/test_phase.py
- python -m pytest -n auto
- pcae health
- pcae check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-19T12:49:48.486496+02:00
