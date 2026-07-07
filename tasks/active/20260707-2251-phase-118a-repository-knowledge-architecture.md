# Task Contract

## Task ID

20260707-2251-phase-118a-repository-knowledge-architecture

## Title

Phase 118A - Repository Knowledge Architecture

## Status

active

## Mode

documentation

## Goal

Design the architecture-only Repository Knowledge foundation for Track B Repository Intelligence without source or runtime behavior changes.

## Allowed Files

- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- docs/PHASE_118_REPOSITORY_KNOWLEDGE_ARCHITECTURE.md
- tasks/active/20260707-2251-phase-118a-repository-knowledge-architecture.md
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

- Repository Knowledge is defined and clearly distinguished from Repository State, Evidence, Advisory Context, Repository Skills, and Decision Evaluation.
- Core primitives, graph model, source attribution, determinism, verification, versioning, read-only boundaries, and future capability emergence are documented.
- No execution, enforcement, shell mediation, runtime behavior, source, or test behavior is changed.

## Acceptance Checks

- pcae health
- pcae check
- pcae doctor task-memory
- pcae push check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-07T22:51:27.339317+02:00
