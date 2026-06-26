# Task Contract

## Task ID

20260626-2032-88s-broker-shell-gate-integration-design

## Title

88S — Broker + Shell Gate Integration Design

## Status

done

## Mode

design

## Goal

Design how the permission broker prototype should consume and interpret shell-gate evidence in a future integration phase. Define integration boundaries, evidence flow, decision priority, hard-block propagation, audit model, and safety invariants. Design-only — no implementation.

## Allowed Files

- docs/PHASE_88_BROKER_SHELL_GATE_INTEGRATION_DESIGN.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**
- tasks/done/**
- tasks/DONE.md

## Forbidden Files

- src/**
- tests/**
- pyproject.toml
- README.md
- docs/LINKEDIN_ARTICLE_DRAFT.md
- docs/REAL_CAPTURED_TASKS.md


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

- docs/PHASE_88_BROKER_SHELL_GATE_INTEGRATION_DESIGN.md exists with version 0.1, implementation_status=not_started
- Shell-gate-to-broker evidence flow, decision mapping, category mapping, and hard-block propagation documented
- No source files modified, no test files modified
- PROJECT_STATUS.md and CHANGELOG.md updated

## Acceptance Checks

- python -m pytest -m fast_green -n auto --tb=no -q

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-26T20:32:46.094646+02:00
