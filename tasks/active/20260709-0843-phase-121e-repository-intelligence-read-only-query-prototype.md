# Task Contract

## Task ID

20260709-0843-phase-121e-repository-intelligence-read-only-query-prototype

## Title

Phase 121E Repository Intelligence Read-Only Query Prototype

## Status

active

## Mode

implementation

## Goal

Implement the first deterministic read-only Repository Intelligence Query prototype for Repository Knowledge Snapshot artifacts, including focused tests and documentation, while preserving observe-only runtime and no execution capability.

## Allowed Files

- src/pcae/repository_intelligence/**
- src/pcae/commands/**
- src/pcae/cli.py
- tests/**
- docs/PHASE_121_REPOSITORY_INTELLIGENCE_QUERY_PROTOTYPE_IMPLEMENTATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/DECISIONS.md
- tasks/active

## Forbidden Files

- schemas/**
- .pcae/repository-intelligence/**


## Allowed Zones

- TBD

## Forbidden Zones

- TBD

## Allowed Dependencies

- core -> core
- commands -> core
- commands -> commands
- cli -> commands
- cli -> core
- tests -> *
- docs -> *
- tasks -> *

## Forbidden Dependencies

- core -> commands
- core -> cli
- core -> tests
- commands -> tests
- cli -> tests

## Enforcement Mode

advisory

## Forbidden Changes

- Do not modify Repository Intelligence schemas.
- Do not generate or modify persisted Repository Intelligence artifacts.
- Do not implement Historical Memory Snapshot, Dependency Knowledge
  Graph, Change Impact, or Advisory Context queries.
- Do not implement a query language, parser grammar, REST surface, API
  server, runtime plugin, AI provider integration, network access,
  repository scanning, graph traversal, dependency reasoning, change
  impact reasoning, execution planning, or execution capability.
- Do not change runtime posture.

## Acceptance Criteria

- Implement read-only snapshot loading and compatibility verification
  for Repository Knowledge Snapshot executable schema version
  119O.1.0-json-schema.
- Implement deterministic structured query evaluation for entity,
  capability, architectural contract, attribution, limitation, and
  boundary lookup.
- Preserve attribution, limitations, boundary disclosures, disclaimers,
  and source metadata in deterministic results.
- Provide the smallest CLI surface for bounded snapshot queries.
- Add focused Query Layer tests and preserve Repository Knowledge
  Snapshot regression behavior.
- Update implementation documentation and project memory.
- Preserve runtime posture as Observed / observe / execution
  unavailable.
- Recommend 121F as the next phase.

## Acceptance Checks

- python -m pytest tests/test_phase_121e_repository_intelligence_query.py -q
- python -m pytest tests/test_phase_120e_repository_knowledge_snapshot.py -q
- pcae health
- pcae check
- pcae doctor task-memory
- pcae runtime inspect
- pcae notify status

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-09T08:43:10.987981+02:00
