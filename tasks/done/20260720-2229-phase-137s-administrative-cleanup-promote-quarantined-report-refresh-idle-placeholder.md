# Task Contract

## Task ID

20260720-2229-phase-137s-administrative-cleanup-promote-quarantined-report-refresh-idle-placeholder

## Title

Phase 137S administrative cleanup: promote quarantined report, refresh idle placeholder

## Status

done

## Mode

documentation

## Goal

Fix the test_results metadata shape so the Phase 137S canonical phase report can be promoted out of quarantine, and refresh the stale post-137R idle task placeholder to correctly reflect post-137S state.

## Allowed Files

- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- .pcae/phase-reports/latest.md
- .pcae/phase-reports/latest.json
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- PROJECT_STATUS.md
- CHANGELOG.md

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

- Phase 137S canonical report is no longer quarantined
- Active idle task correctly reflects post-137S state

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-20T22:29:49.410712+02:00
