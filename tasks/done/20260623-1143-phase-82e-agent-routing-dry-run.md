# Task Contract

## Task ID

20260623-1143-phase-82e-agent-routing-dry-run

## Title

Phase 82E Agent Routing Dry-Run

## Status

done

## Mode

documentation

## Goal

Simulate routing decisions for hypothetical task types against known backends, capabilities, and safety profiles. Dry-run only, no real routing, no backend invocation.

## Allowed Files

- docs/AGENT_ROUTING_DRY_RUN.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active
- tasks/active/*

## Forbidden Files

- docs/REAL_CAPTURED_TASKS.md
- src/**
- tests/**

## Allowed Zones

- TBD

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

strict

## Forbidden Changes

- docs/REAL_CAPTURED_TASKS.md modification
- Source code modification
- Test modification
- Backend invocation
- Real routing

## Acceptance Criteria

- Dry-run artifact exists
- Evaluates all hypothetical task types
- No real routing performed
- No backend invocation

## Acceptance Checks

- pcae health
- pcae check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-23T11:43:22.246475+02:00
