# Task Contract

## Task ID

20260713-1918-phase-135h-lifecycle-integration-and-legacy-authority-retirement-plan

## Title

Phase 135H: Lifecycle Integration and Legacy Authority Retirement Plan

## Status

active

## Mode

plan

## Goal

Re-derive and document the complete planning-only migration from current production lifecycle authority to a production CLTR authority, including retirement, compatibility, shadow, cutover, rollback, schema prerequisites, hazards, and successor authority.

## Allowed Files

- docs/PHASE_135_LIFECYCLE_INTEGRATION_AND_LEGACY_AUTHORITY_RETIREMENT_PLAN.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- tasks/active
- tasks/active/20260713-1918-phase-135h-lifecycle-integration-and-legacy-authority-retirement-plan.md

## Forbidden Files

- src/pcae/core/finalization_transaction.py
- docs/PHASE_135_CANONICAL_LIFECYCLE_TRANSITION_RECORD_CONTRACT.md
- docs/specifications/PFR-001_CANONICAL_PHASE_REPORT_CONTRACT.md


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

- All eleven required planning sections, three non-blocking findings, eight inherited hazards, schema prerequisite, certified-content provenance, and planned-successor investigation are documented.
- No implementation, production integration, authority cutover, schema implementation, execution capability, PFN-001, PFR-001, or CLTR-001 change occurs.
- Project memory records Phase 135H completion and recommends the independently justified next prerequisite phase.

## Acceptance Checks

- pcae health
- pcae check
- pcae doctor task-memory
- pcae push check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-13T19:18:09.461410+02:00
