# Task Contract

## Task ID

20260630-1200-phase-95i1-commit-attribution-hardening

## Title

Phase 95I.1 — Phase Report Commit Attribution Hardening

## Status

active

## Mode

implementation

## Goal

Fix PCAE phase report commit attribution bug: stale prior-phase commits should not be listed as current-phase commits in reports or Telegram notifications.

## Allowed Files

- src/pcae/commands/phase.py
- src/pcae/core/phase_reports.py
- tests/test_phase_reports.py
- docs/PHASE_95I1_PHASE_REPORT_COMMIT_ATTRIBUTION_HARDENING.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/**
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- .pcae/skills/phase-finalization/**
- docs/PHASE_95_SINGLE_BACKEND_ARTIFACT_ONLY_INVOCATION_PROTOTYPE_PLAN.md

## Forbidden Files

- None

## Override Protected Files

- pyproject.toml


## Allowed Zones

- core
- commands
- tests
- docs
- tasks
- config

## Forbidden Zones

- scripts

## Allowed Dependencies

## Forbidden Dependencies

## Enforcement Mode

advisory

## Forbidden Changes

- No real backend invocation
- No adapter execution
- No subprocess execution
- No network call
- No shell interception
- No Telegram inbound
- No enforcement
- No automatic apply
- No apply execution
- No commit/push authorization
- No real AI backend calls

## Acceptance Criteria

- Fix: phase_commits: [] in metadata produces empty commits (not git log fallback)
- Fix: commit ownership validation warns when phase_commits not in metadata
- Fix: COMPLETENESS_COMPLETE preserves trust warnings
- All existing phase report tests pass (backward compatible)
- 7 new commit attribution tests pass
- Backend, notification, bootstrap, fast-green suites pass
- 95I report regenerated without stale commits
- Telegram no longer labels prior-phase commits as "Phase commit"

## Acceptance Checks

- python -m pytest tests/test_phase_reports.py tests/test_phase_reports_cli.py -q -ra passes
- python -m pytest tests/test_notifications.py tests/test_notifications_cli.py tests/test_telegram_notifications.py -q -ra passes
- python -m pytest tests -q -ra -k "bootstrap or session or handoff or notify or phase_report or task_memory or metadata or skill" passes
- python -m pytest tests/test_backend_invocations.py tests/test_backend_cli.py -q -ra passes
- python -m pytest -m "fast_green" -n auto -ra passes
- pcae health passes
- pcae check passes

## Documentation Requirements

- docs/PHASE_95I1_PHASE_REPORT_COMMIT_ATTRIBUTION_HARDENING.md created
- PROJECT_STATUS.md updated
- CHANGELOG.md updated
- tasks/DONE.md updated

## Created Timestamp

2026-06-30T12:00:00.000000+02:00
