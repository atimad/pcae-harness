# Task Contract

## Task ID

20260619-1408-phase-71q-phase-prompt-queue-metadata-preservation

## Title

Phase 71Q Phase Prompt Queue Metadata Preservation

## Status

active

## Mode

implementation

## Goal

Preserve prompt source metadata for prompt-enqueued phase queue items while keeping string-only queue entries compatible.

## Allowed Files

- src/pcae/cli.py
- src/pcae/commands/phase.py
- tests/test_phase.py
- CHANGELOG.md
- PROJECT_STATUS.md
- tasks/active/*71q*.md

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

TBD

## Forbidden Changes

- TBD

## Acceptance Criteria

- Existing string-only queue entries still list, check, and hygiene correctly.
- Prompt-enqueued entries preserve source metadata in structured queue entries.
- Queue list/check JSON includes metadata when available.
- Queue hygiene detects placeholder titles for both string and structured entries.

## Acceptance Checks

- python -m pytest tests/test_phase.py
- python -m pytest -n auto
- pcae health
- pcae check
- pcae doctor task-memory
- pcae push check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-19T14:08:41.559337+02:00
