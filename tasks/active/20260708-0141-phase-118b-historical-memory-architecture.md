# Task Contract

## Task ID

20260708-0141-phase-118b-historical-memory-architecture

## Title

Phase 118B - Historical Memory Architecture

## Status

active

## Mode

documentation

## Goal

Design the architecture-only Historical Memory layer for Track B Repository Intelligence without source, test, runtime, lifecycle, or execution behavior changes.

## Allowed Files

- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- docs/PHASE_118_HISTORICAL_MEMORY_ARCHITECTURE.md
- tasks/active/20260708-0141-phase-118b-historical-memory-architecture.md
- tasks/active
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- TBD


## Allowed Zones

- docs
- tasks
- config

## Forbidden Zones

- core
- commands
- cli
- tests
- scripts
- hooks
- package
- session
- policy

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

advisory

## Forbidden Changes

- TBD

## Acceptance Criteria

- Historical Memory is defined and distinguished from Repository Knowledge, Repository State, Evidence, Advisory Context, Decision Evaluation, and model/conversation memory.
- Core historical primitives, lineage, source attribution, supersession/correction, determinism, verification, versioning, query model, and integrations are documented.
- No historical extraction implementation, database, CLI, dependency graph, change impact analysis, source/test/runtime behavior, execution, enforcement, or lifecycle redesign is added.

## Acceptance Checks

- pcae health
- pcae check
- pcae doctor task-memory
- pcae push check
- pcae runtime inspect --json
- pcae notify status

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-08T01:41:39.544770+02:00
