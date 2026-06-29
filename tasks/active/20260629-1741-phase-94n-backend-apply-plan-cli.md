# Task Contract

## Task ID

20260629-1741-phase-94n-backend-apply-plan-cli

## Title

Phase 94N — Backend Apply Plan CLI

## Status

active

## Mode

implementation

## Goal

Implement safe Backend Apply Plan CLI: show, create, validate apply plan artifacts. Expose the apply plan model from 94K and readiness validator from 94L through CLI commands. No apply execution, no file mutation, no backend invocation.

## Allowed Files

- src/pcae/core/backend_invocations.py
- src/pcae/commands/backend.py
- src/pcae/cli.py
- tests/test_backend_invocations.py
- tests/test_backend_cli.py
- docs/PHASE_94_BACKEND_APPLY_PLAN_CLI.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/20260629-1741-phase-94n-backend-apply-plan-cli.md
- tasks/done/**
- tasks/DONE.md
- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json

## Forbidden Files

- src/pcae/core/apply_execution.py
- src/pcae/core/patch_parser.py

## Allowed Zones

- core
- commands
- cli
- tests
- docs
- tasks
- config

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

advisory

## Forbidden Changes

- No apply execution
- No patch parsing for mutation
- No file mutation outside .pcae/backend-apply-plans/ and .pcae/backend-apply-readiness/
- No backend invocation
- No subprocess execution
- No network calls
- No shell interception or wrappers
- No command mediation
- No Telegram inbound commands
- No remote shell or /run
- No enforcement
- No autonomous mutation
- No automatic apply
- No real AI backend calls
- No new product features beyond apply plan CLI

## Acceptance Criteria

- pcae backend apply-plan show --latest handles missing cleanly
- pcae backend apply-plan create persists artifact
- pcae backend apply-plan validate runs readiness validator
- Hard blocks prevent apply_ready
- JSON output deterministic and secret-safe
- All tests pass

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-29T17:41:52.710257+02:00
