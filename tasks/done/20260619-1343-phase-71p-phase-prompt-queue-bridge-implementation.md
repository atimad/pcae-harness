# Task Contract

## Task ID

20260619-1343-phase-71p-phase-prompt-queue-bridge-implementation

## Title

Phase 71P phase prompt queue bridge implementation

## Status

done

## Mode

implementation

## Goal

Implement safe planning-only bridge from captured phase prompts to the phase queue per 71O design.

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
- No automatic task creation from prompts
- No phase queue execution

## Acceptance Criteria

- Latest prompt can be queued as planning item
- Specific prompt file can be queued
- --dry-run reports without mutation
- --json output includes source, title, queue count
- Missing prompt returns error
- Duplicate detection
- Queue remains planning-only

## Acceptance Checks

- python -m pytest tests/test_phase.py
- python -m pytest -n auto
- pcae health
- pcae check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-19T13:43:36.413357+02:00
