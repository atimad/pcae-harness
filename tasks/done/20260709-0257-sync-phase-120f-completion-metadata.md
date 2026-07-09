# Task Contract

## Task ID

20260709-0257-sync-phase-120f-completion-metadata

## Title

Sync Phase 120F completion metadata

## Status

done

## Mode

maintenance

## Goal

Commit the canonical Phase 120F completion metadata and completion report after successful phase finalization.

## Allowed Files

- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/active
- tasks/active/20260709-0257-sync-phase-120f-completion-metadata.md

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

- Phase 120F canonical completion metadata and report are consistent and committed.

## Acceptance Checks

- pcae phase-report show --latest --trust
- pcae health
- pcae check
- pcae doctor task-memory

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-09T02:57:36.720984+02:00
