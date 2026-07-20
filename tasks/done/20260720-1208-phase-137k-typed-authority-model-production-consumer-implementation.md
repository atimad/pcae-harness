# Task Contract

## Task ID

20260720-1208-phase-137k-typed-authority-model-production-consumer-implementation

## Title

Phase 137K: Typed Authority Model Production Consumer Implementation

## Status

done

## Mode

idle

## Goal

Implement pcae authority inspect <path> per TAMPC-001 v1.0 and the 137J plan

## Allowed Files

- src/pcae/commands/**
- src/pcae/cltr/**
- src/pcae/cli.py
- tests/**
- .pcae/policy.toml
- .pcae/phase-completion-metadata.json
- docs/**
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md

## Forbidden Files

- TBD


## Allowed Zones

- commands
- cltr
- cli
- tests
- docs
- tasks
- config
- policy

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

2026-07-20T12:08:45.422183+02:00
