# Task Contract

## Task ID

20260622-2212-phase-79a-staged-file-aware-implementation-commit-mode

## Title

Phase 79A Staged-File-Aware Implementation Commit Mode

## Status

done

## Mode

implementation

## Goal

Add pcae commit implementation command that commits only explicit paths while preserving unrelated pre-existing staged files.

## Allowed Files

- src/pcae/cli.py
- src/pcae/commands/commit.py
- tests/test_staged_file_aware_commit.py
- CHANGELOG.md
- PROJECT_STATUS.md
- tasks/active
- tasks/active/*

## Forbidden Files

- docs/REAL_CAPTURED_TASKS.md

## Allowed Zones

- TBD

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

strict

## Forbidden Changes

- docs/REAL_CAPTURED_TASKS.md modification
- Backend invocation

## Acceptance Criteria

- pcae commit implementation command exists with --message, --path, --dry-run, --json
- Commits only explicit paths
- Preserves pre-existing staged files
- Blocks protected staged file inclusion
- Never pushes, invokes backend, or runs runner execution

## Acceptance Checks

- python -m pytest tests/test_staged_file_aware_commit.py -x

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-22T22:12:53.768636+02:00
