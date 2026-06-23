# Task Contract

## Task ID

20260623-0851-phase-82c-subagent-discovery-contract

## Title

Phase 82C Subagent Discovery Contract

## Status

done

## Mode

documentation

## Goal

Design the contract for subagent discovery: how PCAE identifies subagents, what metadata is captured, how discovery is authorized, and how results are represented. Design only, no probing or execution.

## Allowed Files

- docs/SUBAGENT_DISCOVERY_CONTRACT.md
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
- Subagent probing

## Acceptance Criteria

- Contract artifact exists
- Defines subagent identity, capability, safety, and discovery models
- No backend invocation or subagent probing
- No routing authorized

## Acceptance Checks

- pcae health
- pcae check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-23T08:51:06.962637+02:00
