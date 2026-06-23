# Task Contract

## Task ID

20260623-0837-phase-82b-agent-identity-capability-probe

## Title

Phase 82B Agent Identity Capability Probe

## Status

active

## Mode

documentation

## Goal

Perform bounded identity/availability probes for known backend commands. Record metadata without sending prompts or executing tasks.

## Allowed Files

- docs/AGENT_IDENTITY_CAPABILITY_PROBE.md
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
- Backend task execution
- Prompt sending

## Acceptance Criteria

- Probe artifact exists
- All four backends probed for availability
- No prompts sent
- No backend task execution
- No routing authorized

## Acceptance Checks

- pcae health
- pcae check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-23T08:37:45.116825+02:00
