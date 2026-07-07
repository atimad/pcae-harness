# Task Contract

## Task ID

20260707-0656-phase-117b-v0-2-test-suite-maintenance-quality-improvements

## Title

Phase 117B - v0.2 Test Suite Maintenance & Quality Improvements

## Status

done

## Mode

implementation

## Goal

Clean up stale/legacy test expectations documented during 116C/116D so PCAE can establish a clean v0.2 quality baseline before release preparation.

## Allowed Files

- tests/**
- docs/**
- tasks/active/**
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/TODO.md
- tasks/DECISIONS.md
- tasks/DONE.md
- .pcae/phase-completion-metadata.json

## Forbidden Files

- src

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

- Reproduce stale/legacy failures documented in 116C/116D.
- Update stale assertions to match the frozen v0.2 architecture without weakening intended coverage.
- Stop and report if any failure reveals a real runtime or lifecycle defect.
- Full suite and fast_green pass, or any remaining failures are explicitly documented non-blockers.
- No runtime behavior change; execution capability remains unavailable.

## Acceptance Checks

- pcae health
- pcae check
- pcae doctor task-memory
- pcae push check
- pcae session bootstrap --compact --profile implementation
- pcae runtime inspect --json
- pcae notify status

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-07T06:56:33.835667+02:00
