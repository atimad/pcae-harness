# Task Contract

## Task ID

20260623-0245-phases-79d-79f-governance-reliability-hardening

## Title

Phases 79D-79F Governance Reliability Hardening

## Status

active

## Mode

implementation

## Goal

Formalize hook-bypass policy, add artifact metadata consistency validator, and improve task-memory auto-reconciliation.

## Allowed Files

- src/pcae/hook_bypass.py
- src/pcae/artifact_metadata.py
- src/pcae/core/tasks.py
- tests/test_hook_bypass_policy.py
- tests/test_artifact_metadata_consistency.py
- tests/test_task_memory_reconciliation.py
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
- Lifecycle state machine implementation

## Acceptance Criteria

- Hook-bypass policy helper exists and is tested
- Artifact metadata validator exists and is tested
- Task-memory reconciliation improvements exist and are tested
- No lifecycle state machine
- No backend invocation

## Acceptance Checks

- python -m pytest tests/test_hook_bypass_policy.py tests/test_artifact_metadata_consistency.py tests/test_task_memory_reconciliation.py -x

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-23T02:45:26.112456+02:00
