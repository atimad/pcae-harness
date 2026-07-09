# Task Contract

## Task ID

20260709-1300-phase-122d-repository-intelligence-advisory-consumption-prototype-plan

## Title

Phase 122D Repository Intelligence Advisory Consumption Prototype Plan

## Status

done

## Mode

planning

## Goal

Define the definitive implementation plan for the first Repository Intelligence Advisory Consumption prototype: a deterministic, read-only Advisory Context Builder consuming Repository Intelligence exclusively through the Track 121 Query Layer, within the boundaries frozen by 122B and verified by 122C, without implementation.

## Allowed Files

- docs/PHASE_122_REPOSITORY_INTELLIGENCE_ADVISORY_CONSUMPTION_PROTOTYPE_PLAN.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/DECISIONS.md
- tasks/active

## Forbidden Files

- src/**
- tests/**
- schemas/**
- .pcae/repository-intelligence/**


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

- Define the prototype objective: first deterministic, read-only Advisory Context Builder that never performs reasoning or decision making.
- Define scope limited to Repository Knowledge Snapshot and Track 121 Query Layer results only; all other Repository Intelligence artifact families deferred.
- Define the nine-stage consumption pipeline as responsibilities only, with no implementation.
- Define planned components with responsibility, inputs, outputs, and boundaries for each, without classes or source layout.
- Define the conceptual Advisory Context Package plan: selected Repository Intelligence, attribution bundle, limitation bundle, boundary disclosure bundle, advisory metadata.
- Define the query interaction plan restricting access to the Track 121 Query Layer only.
- Define attribution, limitation propagation, and boundary propagation plans.
- Define the fail-closed failure plan for missing Repository Intelligence, unsupported snapshot schema, invalid query response, missing attribution, missing limitation, missing boundary disclosure, and corrupted artifact.
- Define the 122F verification plan and measurable 122E acceptance criteria.
- Document risks and mitigation strategies.
- Explicitly defer Historical Memory, Dependency Knowledge Graph, Change Impact, Advisory Intelligence Context Package consumption, graph traversal, dependency reasoning, change impact reasoning, execution planning, and execution capability.
- Introduce no implementation, source code change, test code change, or schema change; preserve runtime posture as Observed / observe / execution unavailable.
- Recommend 122E as the next phase.

## Acceptance Checks

- pcae health
- pcae check
- pcae doctor task-memory
- pcae runtime inspect
- pcae notify status

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-09T13:00:54.541390+02:00
