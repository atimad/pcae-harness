# Task Contract

## Task ID

20260920-1342-phase-150c-pcae-lifecycle-filename-length-hardening-r-bound-phase-report-and-task-contract-filenames

## Title

Phase 150C (PCAE-LIFECYCLE-FILENAME-LENGTH-HARDENING-R): bound phase-report and task-contract filenames

## Status

active

## Mode

implementation

## Goal

Repair the ENAMETOOLONG defect where an unbounded canonical phase ID/task ID is embedded directly into a filesystem path component, by adding src/pcae/core/filename_safety.py and routing phase_reports.write_phase_report/write_quarantined_report and tasks.create_task_contract through it. Fresh independent re-attempt after 150A was blocked by two stale Fast Green assertions, now repaired by 150B. Zero contract changes.

## Allowed Files

- src/pcae/core/filename_safety.py
- src/pcae/core/phase_reports.py
- src/pcae/core/tasks.py
- tests/**
- docs/**
- tasks/**
- .pcae/**
- PROJECT_STATUS.md
- CHANGELOG.md

## Forbidden Files

- docs/contracts/**
- src/pcae/core/hpac_pawa_helper_protocol.py
- src/pcae/core/hpac_pawa_helper_store_adapter.py
- src/pcae/core/hpac_pawa_helper_operations.py


## Allowed Zones

- core
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

- TBD

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-20T13:42:57.254065+02:00
