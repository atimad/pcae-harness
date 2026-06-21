# Task Contract

## Task ID

20260621-1115-phase-77l-backend-created-output-quarantine-review

## Title

Phase 77L: Backend-Created Output Quarantine Review

## Status

done

## Mode

implementation

## Goal

Add a quarantine review command for backend-created output. Verify file existence, metadata match, git status. Must not adopt, stage, commit, push, move, delete, or modify the backend-created file.

## Allowed Files

- src/pcae/cli.py
- src/pcae/commands/phase.py
- tests/test_phase.py
- CHANGELOG.md
- PROJECT_STATUS.md
- tasks/active
- docs/REAL_CAPTURED_TASKS.md

## Explicitly NOT to be staged/committed

- docs/REAL_CAPTURED_TASKS.md (backend-created evidence)

## Acceptance Criteria

- 8 tests pass, python -m pytest -n auto passes
