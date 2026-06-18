# Task Contract

## Task ID

20260618-2237-70s-lifecycle-review-status-in-push-check

## Title

70S Lifecycle Review Status in Push Check

## Status

active

## Mode

implementation

## Goal

Make lifecycle review status visible in push readiness output, advisory-only.

## Allowed Files

- src/pcae/commands/push.py
- src/pcae/core/review.py
- src/pcae/core/templates.py
- tests/test_push.py
- tests/test_review.py
- PROJECT_STATUS.md
- CHANGELOG.md
- docs/COMMANDS.md
- tasks/active/**

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

advisory

## Forbidden Changes

- TBD

## Acceptance Criteria

- Missing LRR is advisory only, does not block push
- Existing push readiness behavior unchanged

## Acceptance Checks

- pcae health
- pcae check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-18T22:37:30.295979+02:00
