# Task Contract

## Task ID

20260710-0224-phase-127a-historical-memory-architecture

## Title

Phase 127A Historical Memory Architecture

## Status

done

## Mode

architecture

## Goal

Define the canonical architecture for Historical Memory: PCAE's temporal layer describing how and why the repository evolved over time, complementing Repository Intelligence's point-in-time description. Architecture only -- no schema change (119Q's historical_memory_snapshot.schema.json is already frozen and is adopted, not modified), no generator, no source code, no test code, no runtime behavior change.

## Allowed Files

- docs/PHASE_127_HISTORICAL_MEMORY_ARCHITECTURE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/20260710-0224-phase-127a-historical-memory-architecture.md

## Forbidden Files

- TBD


## Allowed Zones

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

- Architecture adopts the already-frozen 119Q historical_memory_snapshot.schema.json conceptual model unchanged, mapping every requested conceptual object (Historical Snapshot, Event, Timeline, Relationship, Evidence, Transition, Context) onto its actual $defs
- Defines relationships with Track 119/120/121/122/123/126 consistent with existing schema/README evidence, not invention
- Defines temporal model, determinism, evidence contract, read-only contract, failure model, governance, compatibility, deferred capabilities
- No schema file modified; no source code, test code, generator, or storage introduced
- Known inherited issues carried forward correctly, explicitly noting 126G/126G.1 resolved Telegram issues are not inherited defects
- Runtime remains Observed/observe/execution-unavailable; no implementation occurred

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-10T02:24:11.731778+02:00
