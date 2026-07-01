# Task Contract

## Task ID

20260701-2134-phase-105d-phase-report-trust-gate-hard-fail-push-check-integration

## Title

Phase 105D — Phase Report Trust Gate Hard-Fail / Push-Check Integration

## Status

done

## Mode

implementation

## Goal

Make incomplete phase reports lifecycle-blocking: hard-fail pcae phase complete by default (with --allow-partial-report opt-out), integrate content-completeness trust into pcae push check, keep pcae task finish --commit warning-only pre-push.

## Allowed Files

- src/pcae/core/phase_report_trust.py
- src/pcae/commands/task.py
- src/pcae/commands/phase.py
- src/pcae/commands/push.py
- src/pcae/cli.py
- tests/test_phase.py
- tests/test_phase_report_trust_hard_fail.py
- tests/test_task_finish_notification_ordering.py
- tests/test_task_finish_report_trust_notification.py
- tests/test_phase_report_trust_gate_cli.py
- docs/PHASE_105_PHASE_REPORT_TRUST_HARD_FAIL_PUSH_CHECK_INTEGRATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/**
- tasks/done/**
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- TBD


## Allowed Zones

- core
- tests
- docs
- tasks
- config
- commands
- cli

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

- TBD

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-01T21:34:50.559467+02:00
