# Task Contract

## Task ID

20260706-1740-fix-115m-pushed-state-metadata-field

## Title

Fix 115M pushed-state metadata field

## Status

active

## Mode

implementation

## Goal

Reconcile .pcae/phase-completion-metadata.json pushed_status/origin_main_head_count to reflect the genuinely pushed repository (origin/main..HEAD == 0), and add the missing test_results.report_notification_tests / test_results.bootstrap_session_reporting_tests trust fields the finalization gate requires.

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

- pushed_status reads 'pushed' and origin_main_head_count reads 0, matching live git state; test_results carries report_notification_tests and bootstrap_session_reporting_tests

## Acceptance Checks

- python -m pcae doctor task-memory

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-06T17:40:36.189931+02:00
