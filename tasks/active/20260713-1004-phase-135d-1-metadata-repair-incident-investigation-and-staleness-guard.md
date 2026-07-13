# Task Contract

## Task ID

20260713-1004-phase-135d-1-metadata-repair-incident-investigation-and-staleness-guard

## Title

Phase 135D.1: Metadata-Repair Incident Investigation and Staleness Guard

## Status

active

## Mode

repair

## Goal

Investigate the pcae phase metadata-repair phase_id corruption disclosed during 135D finalization; document full evidence chain; classify 135D's authoritative completion state; implement the smallest justified repair: update the stale .pcae/phase-completion-report.md and add a staleness guard to run_phase_metadata_repair() so it refuses to overwrite metadata when the canonical report disagrees with PROJECT_STATUS.md's actively-maintained Current Phase line.

## Allowed Files

- docs/PHASE_135D.1_METADATA_REPAIR_INCIDENT_INVESTIGATION.md
- .pcae/phase-completion-report.md
- src/pcae/commands/phase.py
- tests/test_finalization_configuration_identity_cross_agent_134b3.py
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/20260713-1004-phase-135d-1-metadata-repair-incident-investigation-and-staleness-guard.md

## Forbidden Files

- TBD


## Allowed Zones

- docs
- tasks
- config
- commands
- tests

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

2026-07-13T10:04:46.608368+02:00
