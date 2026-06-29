# Task Contract

## Task ID

20260629-1721-phase-94m-backend-review-cli

## Title

Phase 94M — Backend Review CLI

## Status

active

## Mode

implementation

## Goal

Implement safe Backend Review CLI: show, create, approve, reject review artifacts. Expose the review state model from 94J through CLI commands. No apply execution, no file mutation, no backend invocation.

## Allowed Files

- src/pcae/core/backend_invocations.py
- src/pcae/commands/backend.py
- src/pcae/cli.py
- tests/test_backend_invocations.py
- tests/test_backend_cli.py
- docs/PHASE_94_BACKEND_REVIEW_CLI.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/20260629-1721-phase-94m-backend-review-cli.md
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
- No file mutation outside .pcae/backend-reviews/
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
- No new product features beyond review CLI

## Acceptance Criteria

- pcae backend review show --latest handles missing cleanly
- pcae backend review create persists artifact
- pcae backend review approve creates approval artifact
- pcae backend review reject creates rejection artifact
- Hard blocks prevent effective approval
- Accepted risk cannot override hard blocks
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

2026-06-29T17:21:17.283987+02:00
