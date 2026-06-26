# Task Contract

## Task ID

20260626-0437-88n-4-full-suite-bottleneck-elimination

## Title

88N.4 — Full Suite Bottleneck Elimination

## Status

done

## Mode

test_governance

## Goal

Reduce full-suite runtime by identifying and eliminating the main bottlenecks while preserving coverage and keeping the full-suite baseline green.

## Allowed Files

- tests/**
- docs/PHASE_88_FULL_SUITE_BOTTLENECK_ELIMINATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**
- tasks/done/**
- tasks/DONE.md

## Forbidden Files

- README.md
- docs/LINKEDIN_ARTICLE_DRAFT.md
- docs/REAL_CAPTURED_TASKS.md
- src/pcae/core/backend_preflight.py
- .githooks/**


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

- Full suite passes green after optimization
- Runtime profiling completed and bottleneck map documented
- Quick tier passes

## Acceptance Checks

- pcae health
- pcae check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-26T04:37:13.299245+02:00
