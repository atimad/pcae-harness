# Task Contract

## Task ID

20260710-0211-phase-126g-1-telegram-commit-trust-metadata-repair

## Title

Phase 126G.1 Telegram Commit Trust Metadata Repair

## Status

done

## Mode

implementation

## Goal

Repair commit metadata propagation so commit ownership can be fully trusted by the report trust validator, eliminating the 'commits.phase_owned not verified — no phase_commits in metadata' warning. Root cause: pcae phase-report create (126G) sets report.commits from --commit flags but never declares report.metadata['commit_attribution'], which is the specific field assess_completeness() checks for commit-ownership verification. Repair only this commit trust metadata propagation gap; do not touch canonical report generation, formatting, governance/test/no-go metadata, or notification formatting.

## Allowed Files

- src/pcae/commands/phase_reports.py
- tests/test_phase_reports.py
- tests/test_telegram_notifications.py
- docs/PHASE_126G1_TELEGRAM_COMMIT_TRUST_METADATA_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/20260710-0211-phase-126g-1-telegram-commit-trust-metadata-repair.md

## Forbidden Files

- TBD


## Allowed Zones

- commands
- tests
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

- pcae phase-report create declares report.metadata['commit_attribution'] when --commit flags are supplied, satisfying assess_completeness()'s commit-ownership check honestly
- commits.phase_owned not verified warning no longer appears when commits were explicitly supplied via --commit
- Warning correctly remains when commits genuinely cannot be attributed (no --commit supplied) -- no false-negative suppression
- Canonical report generation, formatting, governance/test/no-go metadata, and notification formatting unchanged
- report_notification_tests, report trust tests, Telegram notification tests, phase finalization tests, fast_green all pass
- No Dependency Knowledge Graph, Repository Intelligence, Historical Memory, execution, runtime plugin, Advisory, Decision Evaluation, or schema file modified
- Runtime remains Observed/observe/execution-unavailable

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-10T02:11:52.178269+02:00
