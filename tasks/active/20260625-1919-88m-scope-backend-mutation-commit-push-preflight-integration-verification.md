# Task Contract

## Task ID

20260625-1919-88m-scope-backend-mutation-commit-push-preflight-integration-verification

## Title

88M — Scope + Backend + Mutation + Commit/Push Preflight Integration Verification

## Status

active

## Mode

integration_verification

## Goal

Verify that all explicit preflight commands work together as a coherent read-only governance surface. Add integration tests and a verification artifact demonstrating that scope, backend, mutation/adoption, commit, and push preflights preserve consistent non-authorizing behavior, safety flags, evidence flow, reason-code semantics, and no-write/no-execution guarantees.

## Allowed Files

- tests/**
- src/pcae/core/scope_preflight.py
- src/pcae/core/backend_preflight.py
- src/pcae/core/mutation_preflight.py
- src/pcae/core/commit_push_preflight.py
- docs/PHASE_88_PREFLIGHT_INTEGRATION_VERIFICATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**
- tasks/completed/**
- tasks/done/**

## Forbidden Files

- README.md
- docs/REAL_CAPTURED_TASKS.md
- .pcae/**


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

- TBD

## Acceptance Criteria

- All five preflight commands registered tests pass
- JSON envelope consistency tests pass
- Safety flag consistency tests pass
- All commands are non-authorizing tests pass
- No storage/no .pcae/cache/state tests pass
- Quick tier passes
- Full suite passes
- docs/PHASE_88_PREFLIGHT_INTEGRATION_VERIFICATION.md exists
- Readiness decision recorded

## Acceptance Checks

- pcae health
- pcae check
- python -m pytest -n auto

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-25T19:19:31.486401+02:00
