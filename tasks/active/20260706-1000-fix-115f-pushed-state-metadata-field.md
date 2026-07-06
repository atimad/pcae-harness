# Task Contract

## Task ID

20260706-1000-fix-115f-pushed-state-metadata-field

## Title

Fix 115F pushed-state metadata field

## Status

active

## Mode

implementation

## Goal

Correct governance_results.pcae_push_check and pushed_status/origin_main_head_count to reflect the genuinely pushed state, then re-run pcae phase complete

## Allowed Files

- .pcae/phase-completion-metadata.json
- tasks/active/20260706-1000-fix-115f-pushed-state-metadata-field.md

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

- canonical latest.json phase_id == 115F

## Acceptance Checks

- true

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-06T10:00:32.902366+02:00
