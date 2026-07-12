# Task Contract

## Task ID

20260712-1037-phase-134e-10-1-1-phase-owned-commit-attribution-repair

## Title

Phase 134E.10.1.1: Phase-Owned Commit Attribution Repair

## Status

active

## Mode

implementation

## Goal

Repair the commit-attribution defect in 134E.10.1's own governed report (1844b05b incorrectly attributed, a prior 134E.10V commit). Remove the blind _gather_commits() fallback in phase.py; add a generic cross-phase-commit-contamination check wired into phase.py and task.py. Issue as a distinct corrective report, not a second ordinary 134E.10.1 completion. Do not begin 134E.10.1V or 134F.

## Allowed Files

- docs/PHASE_134_PHASE_OWNED_COMMIT_ATTRIBUTION_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- src/pcae/commands/phase.py
- src/pcae/commands/task.py
- src/pcae/core/phase_reports.py
- tests/test_rc_audit_findings_repair.py
- tests/test_commit_attribution_repair_134e10_1_1.py
- tasks/active/20260712-1037-phase-134e-10-1-1-phase-owned-commit-attribution-repair.md

## Forbidden Files

- TBD


## Allowed Zones

- docs
- tasks
- core
- commands
- tests

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

TBD

## Forbidden Changes

- TBD

## Acceptance Criteria

- TBD

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-12T10:37:16.283758+02:00
