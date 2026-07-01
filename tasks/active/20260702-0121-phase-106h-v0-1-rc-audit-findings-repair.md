# Task Contract

## Task ID

20260702-0121-phase-106h-v0-1-rc-audit-findings-repair

## Title

Phase 106H: v0.1 RC Audit Findings Repair

## Status

active

## Mode

implementation

## Goal

Repair the trust-gate asymmetry between pcae task finish --commit and pcae phase complete found in Phase 106G's audit, using a shared helper so both paths enforce the same hard-fail completeness rules

## Allowed Files

- src/pcae/core/phase_report_trust.py
- src/pcae/commands/task.py
- src/pcae/commands/phase.py
- docs/PHASE_106_RC_AUDIT_FINDINGS_REPAIR.md
- docs/V0_1_GOLDEN_WORKFLOW.md
- docs/RELEASE_SCOPE_V0_1.md
- docs/RELEASE_HANDOFF_V0_1_RC1.md
- tests/test_rc_audit_findings_repair.py
- tests/test_task_finish_report_trust_notification.py
- tests/test_task_finish_notification_ordering.py
- tests/test_phase_report_trust_hard_fail.py
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md

## Forbidden Files

- TBD


## Allowed Zones

- core
- commands
- docs
- tests
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

- TBD

## Acceptance Criteria

- TBD

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-02T01:21:33.508483+02:00
