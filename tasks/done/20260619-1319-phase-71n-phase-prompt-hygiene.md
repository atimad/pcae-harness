# Task Contract

## Task ID

20260619-1319-phase-71n-phase-prompt-hygiene

## Title

Phase 71N phase prompt hygiene

## Status

done

## Mode

implementation

## Goal

Add safe phase prompt hygiene for inspection and optional pruning/clearing of stale or placeholder prompts.

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
- No automatic clearing without explicit confirmation

## Acceptance Criteria

- prompt-hygiene reports no issues for absent/empty prompt store
- prompt-hygiene reports placeholder-like prompts when present
- placeholder clearing requires --clear-placeholders --confirm
- real non-placeholder prompts are not cleared
- prompt-prune dry-run reports candidates without deleting
- prompt-prune confirm deletes only older timestamped artifacts
- latest.md/latest.json are preserved by prune
- --json works where implemented

## Acceptance Checks

- python -m pytest tests/test_phase.py
- python -m pytest -n auto
- pcae health
- pcae check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-19T13:19:50.328099+02:00
