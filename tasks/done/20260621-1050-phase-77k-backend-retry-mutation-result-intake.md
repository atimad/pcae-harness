# Task Contract

## Task ID

20260621-1050-phase-77k-backend-retry-mutation-result-intake

## Title

Phase 77K: Backend Retry Mutation Result Intake

## Status

done

## Mode

implementation

## Goal

Add a mutation-aware intake command for the 77J governed retry result. Classify the result, preserve the untracked backend-created file as evidence. Must not modify, delete, stage, commit, or push the backend-created file.

## Allowed Files

- src/pcae/cli.py
- src/pcae/commands/phase.py
- tests/test_phase.py
- CHANGELOG.md
- PROJECT_STATUS.md
- tasks/active
- docs/REAL_CAPTURED_TASKS.md
- .gitignore

## Acceptance Criteria

- 10 tests pass, python -m pytest -n auto passes
