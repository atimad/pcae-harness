# Task Contract

## Task ID

20260630-0117-phase-95d-claude-runtime-evidence-import-cli

## Title

Phase 95D — Claude Runtime Evidence Import CLI

## Status

active

## Mode

implementation

## Goal

Phase 95D — Claude Runtime Evidence Import CLI

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- src/pcae/cli.py
- src/pcae/commands/backend.py
- src/pcae/core/backend_invocations.py
- tests/test_backend_invocations.py
- docs/PHASE_95_CLAUDE_RUNTIME_EVIDENCE_IMPORT_CLI.md

## Forbidden Files

- TBD

## Override Protected Files

- pyproject.toml


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

- No runtime invocation
- No prompt execution
- No source behavior changes outside task/session/handoff governance
- No execution authorization
- No commit
- No push
- No rollback

## Acceptance Criteria

- TBD

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-30T01:17:26.920100+02:00
