# Task Contract

## Task ID

20260709-0805-phase-121d-repository-intelligence-query-prototype-plan

## Title

Phase 121D Repository Intelligence Query Prototype Plan

## Status

active

## Mode

implementation

## Goal

Produce the definitive implementation plan for the first deterministic read-only Repository Intelligence Query prototype over Repository Knowledge Snapshot artifacts, without implementation changes.

## Allowed Files

- docs/PHASE_121_REPOSITORY_INTELLIGENCE_QUERY_PROTOTYPE_PLAN.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/DECISIONS.md
- tasks/active

## Forbidden Files

- src/**
- schemas/**
- tests/**
- .pcae/repository-intelligence/**


## Allowed Zones

- docs
- tasks

## Forbidden Zones

- core
- commands
- cli
- tests

## Allowed Dependencies

- docs -> docs
- docs -> tasks
- tasks -> docs
- tasks -> tasks

## Forbidden Dependencies

- docs -> core
- docs -> commands
- docs -> cli
- docs -> tests
- tasks -> core
- tasks -> commands
- tasks -> cli
- tasks -> tests

## Enforcement Mode

advisory

## Forbidden Changes

- Do not implement a query engine.
- Do not implement a query parser or query language.
- Do not add CLI, REST, API, Python model, validator, or runtime plugin
  behavior.
- Do not modify source code, schema files, or tests.
- Do not change runtime behavior or execution capability.

## Acceptance Criteria

- Create the Phase 121D prototype plan document.
- Define the planned query pipeline, conceptual components, request
  model, result model, compatibility plan, attribution plan, unknown
  handling, failure plan, persistence interaction, 121F verification
  plan, and 121E acceptance criteria.
- Defer all non-snapshot artifact families and all reasoning/execution
  capabilities.
- Update project memory and task memory.
- Preserve runtime posture as Observed / observe / execution
  unavailable.
- Recommend 121E as the next phase.

## Acceptance Checks

- git status --short
- git status --branch --short
- git log --oneline origin/main..HEAD
- git rev-list --count origin/main..HEAD
- pcae health
- pcae check
- pcae doctor task-memory
- pcae runtime inspect
- pcae notify status

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-09T08:05:41.343557+02:00
