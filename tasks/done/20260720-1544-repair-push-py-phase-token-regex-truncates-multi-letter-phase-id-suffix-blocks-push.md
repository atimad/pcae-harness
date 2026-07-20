# Task Contract

## Task ID

20260720-1544-repair-push-py-phase-token-regex-truncates-multi-letter-phase-id-suffix-blocks-push

## Title

Phase 137MV.1 — Repair: push.py phase-token regex truncates multi-letter phase-ID suffix (blocks push)

## Status

done

## Mode

idle

## Goal

Repair: push.py phase-token regex truncates multi-letter phase-ID suffix (blocks push)

## Allowed Files

- src/pcae/commands/push.py
- tests/**
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json

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

strict

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

2026-07-20T15:44:36.386306+02:00
