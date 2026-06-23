# Task Contract

## Task ID

20260623-1301-phase-83a-multi-agent-task-contract

## Title

Phase 83A Multi-Agent Task Contract

## Status

active

## Mode

documentation

## Goal

Design the formal contract format for PCAE multi-agent tasks. Design only, no routing, invocation, or execution.

## Allowed Files

- docs/MULTI_AGENT_TASK_CONTRACT.md
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
- Real routing or task splitting

## Acceptance Criteria

- Contract design artifact exists
- Defines required fields, role model, approval boundaries, validation rules
- No backend invocation or real routing

## Acceptance Checks

- pcae health
- pcae check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-23T13:01:05.634092+02:00
