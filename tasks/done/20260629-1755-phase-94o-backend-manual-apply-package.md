# Task Contract

## Task ID

20260629-1755-phase-94o-backend-manual-apply-package

## Title

Phase 94O — Backend Manual Apply Package

## Status

done

## Mode

implementation

## Goal

Implement safe Backend Manual Apply Package: model, persistence (JSON+Markdown), and CLI show/create. Package bundles evidence from apply-plan + readiness assessment into a human-readable artifact for manual operator action. No apply execution, no file mutation, no backend invocation.

## Allowed Files

- src/pcae/core/backend_invocations.py
- src/pcae/commands/backend.py
- src/pcae/cli.py
- tests/test_backend_invocations.py
- tests/test_backend_cli.py
- docs/PHASE_94_BACKEND_MANUAL_APPLY_PACKAGE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/20260629-1755-phase-94o-backend-manual-apply-package.md
- tasks/done/**
- tasks/DONE.md
- .pcae/.gitignore
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
- No file mutation outside .pcae/backend-manual-apply-packages/
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
- No automatic test execution
- No automatic pcae check
- No new product features beyond manual apply package

## Acceptance Criteria

- pcae backend manual-apply-package show --latest handles missing cleanly
- pcae backend manual-apply-package create persists JSON and Markdown
- Package defaults no_execution_performed=True
- JSON and Markdown are secret-safe
- All tests pass

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-29T17:55:24.080047+02:00
