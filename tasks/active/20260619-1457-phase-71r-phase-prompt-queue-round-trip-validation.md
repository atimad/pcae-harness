# Task Contract

## Task ID

20260619-1457-phase-71r-phase-prompt-queue-round-trip-validation

## Title

Phase 71R Phase Prompt Queue Round-Trip Validation

## Status

active

## Mode

implementation

## Goal

Add a read-only prompt queue round-trip validation command for captured prompt planning without mutating prompt artifacts, queue state, or task contracts.

## Allowed Files

- src/pcae/cli.py
- src/pcae/commands/phase.py
- tests/test_phase.py
- CHANGELOG.md
- PROJECT_STATUS.md
- tasks/active/*71r*.md

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

- Command reports ready when latest prompt exists and dry-run enqueue can derive a queue item.
- Command reports not ready when no prompt exists.
- Command is read-only and does not mutate prompt artifacts, queue, or tasks.
- JSON output includes prompt_present, queue_present, dry_run_title, ready, and reasons.

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

2026-06-19T14:57:14.767484+02:00
