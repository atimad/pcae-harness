# Task Contract

## Task ID

20260619-1518-phase-71s-codex-autonomy-comparison-handoff-note

## Title

Phase 71S Codex Autonomy Comparison Handoff Note

## Status

done

## Mode

implementation

## Goal

Add a lightweight documentation note defining PCAE agent autonomy comparison criteria, expected report shape, and observed Codex stop-and-recover behavior.

## Allowed Files

- docs/ARCHITECTURE.md
- docs/AUTONOMY.md
- CHANGELOG.md
- PROJECT_STATUS.md
- tasks/active/*71s*.md

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

- Documentation identifies comparison criteria for Claude vs Codex autonomy.
- Documentation defines expected autonomy run report fields.
- Documentation notes that PCAE governance is agent-neutral.
- Documentation captures 71Q/71Q.1/71R Codex stop-and-recover observations.
- Documentation distinguishes agent behavior from Codex sandbox Git-lock permission behavior.

## Acceptance Checks

- python -m pytest -n auto
- pcae health
- pcae check
- pcae doctor task-memory
- pcae push check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-19T15:18:11.857937+02:00
