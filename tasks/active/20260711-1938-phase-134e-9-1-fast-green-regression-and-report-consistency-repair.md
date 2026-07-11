# Task Contract

## Task ID

20260711-1938-phase-134e-9-1-fast-green-regression-and-report-consistency-repair

## Title

Phase 134E.9.1 Fast-Green Regression and Report-Consistency Repair

## Status

active

## Mode

implementation

## Goal

Reproduce, identify, classify, and repair the 4389/4390 fast-green discrepancy between 134E.8V and 134E.9. Root cause: test_pytest_dry_run_not_blocked in tests/test_dry_run_simulation.py is non-hermetic (evaluates against live REPO_ROOT task-lifecycle state via build_simulation), not a genuine 134E.9 regression -- confirmed via read-only detached worktree comparison at the 134E.8V commit. Repair test isolation without weakening the broker's correct fail-closed behavior. Additionally repair validate_derived_correctness() to validate the actual value of the mandatory test_results['fast_green'] field (previously checked only for presence), closing the gap that let 134E.9's own report reach complete status despite its own embedded evidence stating a failure. Corrects the historical over-claim without overwriting or deleting the original 134E.9 report. Completes as its own new phase identity (134E.9.1), not a resend of 134E.9. Do not begin 134E.9V or 134E.10.

## Allowed Files

- src/pcae/core/phase_reports.py
- src/pcae/commands/phase_reports.py
- tests/test_dry_run_simulation.py
- tests/test_architecture_status_generation_independent_verification_134e8v.py
- tests/test_report_consistency_derived_correctness_134e9.py
- docs/PHASE_134_FAST_GREEN_REGRESSION_REPORT_CONSISTENCY_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active
- tasks/active/20260711-1938-phase-134e-9-1-fast-green-regression-and-report-consistency-repair.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- .pcae/phase-metadata-repairs.log

## Forbidden Files

- TBD


## Allowed Zones

- core
- commands
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

TBD

## Forbidden Changes

- TBD

## Acceptance Criteria

- exact failing test identified and fixed at its source (test isolation), not hidden or removed from fast_green
- validate_derived_correctness() blocks a nonzero fast_green failure count with no escape hatch
- fast_green passes 4391/4391 with zero failures, confirmed deterministic across 3 consecutive runs
- original 134E.9 report preserved unmodified; this phase completes under its own new identity 134E.9.1

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-11T19:38:51.382978+02:00
