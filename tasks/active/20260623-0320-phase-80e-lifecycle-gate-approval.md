# Task Contract

## Task ID

20260623-0320-phase-80e-lifecycle-gate-approval

## Title

Phase 80E Lifecycle Gate Approval

## Status

active

## Mode

implementation

## Goal

Add a lifecycle gate approval command that records human approval for a named gate without executing it. Approval is separate from execution; execution_authorized=false always.

## Allowed Files

- src/pcae/lifecycle.py
- src/pcae/commands/lifecycle.py
- src/pcae/cli.py
- tests/test_lifecycle_gate_approval.py
- CHANGELOG.md
- PROJECT_STATUS.md
- tasks/active
- tasks/active/*

## Forbidden Files

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

strict

## Forbidden Changes

- docs/REAL_CAPTURED_TASKS.md modification
- Backend invocation
- Gate execution
- execution_authorized=true

## Acceptance Criteria

- Gate approval command exists
- Requires gate, approved-by, reason
- Records approval separately from execution
- Never executes gates
- execution_authorized=false always
- Supports JSON and dry-run

## Acceptance Checks

- python -m pytest tests/test_lifecycle_gate_approval.py -x

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-23T03:20:24.515391+02:00
