# Task Contract

## Task ID

20260622-2056-phase-77v-1-final-verification-tooling-push-decision

## Title

Phase 77V.1 Final Verification Tooling Push Decision

## Status

active

## Mode

implementation

## Goal

Close repository hygiene after the adoption lifecycle. Keep the 77V final-verification tooling, verify the only unpushed commits are 77V tooling/closure commits, approve pushing them, and push via governed command.

## Allowed Files

- src/pcae/cli.py
- src/pcae/commands/phase.py
- tests/test_phase.py
- tasks/active
- tasks/active/*
- tasks/done/*
- tasks/DONE.md
- CHANGELOG.md
- PROJECT_STATUS.md

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

## Acceptance Criteria

- 77V tooling commits detected and approved
- Unexpected commits block push
- Dirty working tree blocks push
- Adoption lifecycle verified as closed
- Docs file SHA256 matches across working tree/HEAD/origin
- Hook bypass reconciliation verified, not normalized
- Push via governed command only
- After push: origin/main..HEAD count=0, working tree clean

## Acceptance Checks

- python -m pytest tests/test_phase.py -k 77v1

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-22T20:56:18.620505+02:00
