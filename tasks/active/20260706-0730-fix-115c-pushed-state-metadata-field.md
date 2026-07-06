# Task Contract

## Task ID

20260706-0730-fix-115c-pushed-state-metadata-field

## Title

Fix 115C pushed-state metadata field

## Status

active

## Mode

implementation

## Goal

Correct governance_results.pcae_push_check and pushed_status/origin_main_head_count to reflect the genuinely pushed state, then re-run pcae phase complete to promote the canonical report

## Allowed Files

- .pcae/phase-completion-metadata.json
- tasks/active/20260706-0730-fix-115c-pushed-state-metadata-field.md

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

- canonical latest.json phase_id == 115C

## Acceptance Checks

- true

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-06T07:30:25.703356+02:00
