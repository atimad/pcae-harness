# Task Contract

## Task ID

20260709-1038-phase-122a-repository-intelligence-advisory-consumption-architecture

## Title

Phase 122A Repository Intelligence Advisory Consumption Architecture

## Status

done

## Mode

architecture

## Goal

Define the architecture for how the Advisory subsystem may consume Repository Intelligence as structured advisory context through the Track 121 read-only Query Layer, without changing Advisory authority, Decision Evaluation authority, Repository State authority, Evidence authority, or execution boundaries.

## Allowed Files

- docs/PHASE_122_REPOSITORY_INTELLIGENCE_ADVISORY_CONSUMPTION_ARCHITECTURE.md
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

- Document Track 122 purpose: Repository Intelligence becomes structured advisory context without replacing Advisory reasoning or Decision Evaluation.
- Document relationships to Track 119 schemas, Track 120 Repository Knowledge Snapshot, Track 121 Query Layer, Advisory, Advisory Runtime, Repository State, Evidence, Decision Evaluation, and Runtime.
- Define architectural scope: permitted and forbidden operations for the Advisory consumption layer.
- Define the nine-stage advisory consumption pipeline as responsibilities only, with no implementation.
- Define the context model, attribution architecture, limitation architecture, boundary architecture, governance architecture, and failure architecture.
- Document Track 122 roadmap (122A-122F) and future extensibility without coupling implementation.
- Introduce no implementation, source code change, test code change, or schema change; preserve runtime posture as Observed / observe / execution unavailable.
- Recommend 122B as the next phase.

## Acceptance Checks

- pcae health
- pcae check
- pcae doctor task-memory
- pcae runtime inspect
- pcae notify status

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-09T10:38:46.178304+02:00
