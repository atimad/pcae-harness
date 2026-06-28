# Task Contract

## Task ID

20260628-2346-92a-phase-report-artifact-model

## Title

92A — Phase Report Artifact Model

## Status

done

## Mode

implementation

## Goal

Implement a local, durable phase report artifact model for PCAE Production v1. Create structured report objects, validate them, render Markdown/JSON, and write to .pcae/phase-reports/.

## Allowed Files

- src/pcae/core/phase_reports.py
- src/pcae/commands/phase_reports.py
- src/pcae/cli.py
- tests/test_phase_reports.py
- tests/test_phase_reports_cli.py
- docs/PHASE_92_PHASE_REPORT_ARTIFACT_MODEL.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md

## Forbidden Files

- .githooks/**
- docs/LINKEDIN_ARTICLE_DRAFT.md
- docs/REAL_CAPTURED_TASKS.md

## Allowed Zones

- core
- commands
- cli
- tests
- docs
- tasks

## Forbidden Zones

- hooks
- config
- session
- policy
- package
- scripts

## Enforcement Mode

advisory

## Acceptance Criteria

- PhaseReport dataclass with all required fields
- validate/write/render functions
- CLI: pcae phase-report create/show
- Tests covering all behaviors
- Fast-green passes

## Acceptance Checks

- python -m pytest tests/test_phase_reports.py tests/test_phase_reports_cli.py -q -ra
- python -m pytest -m "fast_green" -n auto -ra --durations=100
- pcae health && pcae check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-28T23:46:39.333237+02:00
