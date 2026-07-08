# Task Contract

## Task ID

20260708-2348-repair-phase-119z-recommended-next-phase-metadata-formatting

## Title

Repair Phase 119Z recommended_next_phase metadata formatting

## Status

active

## Mode

implementation

## Goal

Work around an inherited phase-id backward-check bug in pcae phase complete that misclassifies 119AA as earlier than 119Z due to naive letter-branch string comparison, by reformatting the recommended_next_phase metadata string so it does not match the tool's leading-digit regex

## Allowed Files

- .pcae/phase-completion-metadata.json

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

TBD

## Forbidden Changes

- TBD

## Acceptance Criteria

- pcae phase complete no longer strips recommended_next_phase for 119Z

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-08T23:48:15.373288+02:00
