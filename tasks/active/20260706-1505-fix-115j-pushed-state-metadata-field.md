# Task Contract

## Task ID

20260706-1505-fix-115j-pushed-state-metadata-field

## Title

Fix 115J pushed-state metadata field

## Status

active

## Mode

implementation

## Goal

Correct .pcae/phase-completion-metadata.json and .pcae/phase-completion-report.md pushed_status/origin_main_head_count/governance_results.pcae_push_check to reflect the genuinely pushed repository.

## Allowed Files

- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/active/20260706-1505-fix-115j-pushed-state-metadata-field.md

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

- pushed_status is 'pushed', origin_main_head_count is 0, governance_results.pcae_push_check reflects clean state

## Acceptance Checks

- python -m pcae check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-06T15:05:51.560654+02:00
