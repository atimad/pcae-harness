# Task Contract

## Task ID

20260706-1742-repair-115m-phase-report-trust-fields

## Title

Repair 115M phase report trust fields

## Status

done

## Mode

implementation

## Goal

Add the missing report_notification_tests and bootstrap_session_reporting_tests entries to .pcae/phase-completion-metadata.json's validation_results list -- pcae phase complete builds its trust-checked test_results dict from validation_results, not the separate top-level test_results field, so those two required base test-result keys were missing from the array pcae phase complete actually reads.

## Allowed Files

- .pcae/phase-completion-metadata.json

## Forbidden Files

- TBD


## Allowed Zones

- config
- docs
- tasks

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

- validation_results contains entries named report_notification_tests and bootstrap_session_reporting_tests

## Acceptance Checks

- python -m pcae doctor task-memory

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-06T17:42:20.451338+02:00
