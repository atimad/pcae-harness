# Task: Phase 88D.1 — Test Runtime Tiering and Optimization

## Objective

Reduce test feedback time by adding selectable test tiers without weakening
the full suite. Profile, add markers, document tiers.

## Allowed Files

- tests/**
- src/pcae/cli.py
- src/pcae/commands/test_runner.py
- src/pcae/core/docs.py
- pyproject.toml
- docs/TESTING_STRATEGY.md
- docs/COMMANDS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/88d1-test-runtime-tiering.md
- tasks/completed/88d-backend-invocation-preflight-design.md

## Override Protected Files

- pyproject.toml

## Forbidden Files

- README.md
- docs/LINKEDIN_ARTICLE_DRAFT.md
- docs/REAL_CAPTURED_TASKS.md
- .pcae/**
- .githooks/**

## Acceptance Criteria

- Full suite still passes
- Quick and governance tiers exist
- Slow/phase_closure tests marked
- No tests deleted
- docs/TESTING_STRATEGY.md exists

## Status

- [x] Created
- [x] In Progress
- [x] Complete
