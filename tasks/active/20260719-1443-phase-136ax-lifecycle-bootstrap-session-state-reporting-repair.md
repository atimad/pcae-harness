# Task Contract

## Task ID

20260719-1443-phase-136ax-lifecycle-bootstrap-session-state-reporting-repair

## Title

Phase 136AX: Lifecycle Bootstrap & Session State Reporting Repair

## Status

active

## Mode

implementation

## Goal

Repair lifecycle bootstrap, session-state derivation, and reporting defects (current-phase parsing, recommended-next-phase parsing/truncation, phase-completion metadata defensive handling) that produced incomplete, stale, truncated, or internally inconsistent PCAE status output. Governance infrastructure only; no Stage 3 schema/typed-authority-model changes.

## Allowed Files

- src/pcae/core/phase_reports.py
- src/pcae/core/architecture_status.py
- src/pcae/core/status.py
- src/pcae/core/context.py
- src/pcae/core/tasks.py
- src/pcae/commands/phase.py
- src/pcae/commands/task.py
- src/pcae/commands/session.py
- tests/test_phase_136ax_lifecycle_bootstrap_reporting_repair.py
- tests/test_rc_audit_findings_repair.py
- docs/PHASE_136_LIFECYCLE_BOOTSTRAP_SESSION_STATE_REPORTING_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-metadata-repairs.log
- .pcae/phase-reports/**

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

- TBD

## Acceptance Criteria

- session bootstrap, health, check, status coherence, and Architecture Status agree on current/latest-completed/recommended-next phase for live repo state, with reproduced root causes documented and fixed

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes (no new regressions)

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-19T14:43:43.351148+02:00
