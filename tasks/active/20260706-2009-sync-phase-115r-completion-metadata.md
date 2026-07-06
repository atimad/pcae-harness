# Task Contract

## Task ID

20260706-2009-sync-phase-115r-completion-metadata

## Title

Sync phase 115R completion metadata

## Status

active

## Mode

implementation

## Goal

Sync .pcae/phase-completion-metadata.json and .pcae/phase-completion-report.md to reflect Phase 115R — Advisory Repository Skills Prototype (currently stale at 115Q), resolving the phase_identity_consistency/report_completeness rejection from the first task-finish attempt.

## Allowed Files

- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/active/20260706-2009-sync-phase-115r-completion-metadata.md

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

- phase-completion-metadata.json phase_id reads 115R with accurate pushed_status/origin_main_head_count/report_completeness and complete validation_results/test_results trust fields

## Acceptance Checks

- python -m pcae doctor task-memory

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-06T20:09:31.501644+02:00
