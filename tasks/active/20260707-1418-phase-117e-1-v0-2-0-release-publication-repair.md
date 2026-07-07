# Task Contract

## Task ID

20260707-1418-phase-117e-1-v0-2-0-release-publication-repair

## Title

Phase 117E.1 - v0.2.0 Release Publication Repair

## Status

active

## Mode

implementation

## Goal

Repair the gap discovered after intended v0.2.0 release publication by publishing only missing release artifacts and reconciling canonical repository state with actual external publication.

## Allowed Files

- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/TODO.md
- tasks/DECISIONS.md
- tasks/DONE.md
- tasks/active/**
- docs/PHASE_117E_1_RELEASE_PUBLICATION_REPAIR.md
- docs/RELEASE_NOTES_V0_2_0.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- src
- pyproject.toml


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

- Official v0.2.0 release publicly exists.
- Git tag verified locally and remotely.
- GitHub Release verified and references v0.2.0.
- Canonical metadata consistent and audit trail preserved without rewriting history.
- Repository clean, governance healthy, execution unavailable.

## Acceptance Checks

- pcae health
- pcae check
- pcae doctor task-memory
- pcae push check
- pcae session bootstrap --compact --profile implementation
- pcae runtime inspect --json

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-07T14:18:56.893173+02:00
