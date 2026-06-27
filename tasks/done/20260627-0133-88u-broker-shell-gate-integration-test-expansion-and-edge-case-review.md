# Task Contract

## Task ID

20260627-0133-88u-broker-shell-gate-integration-test-expansion-and-edge-case-review

## Title

88U — Broker + Shell Gate Integration Test Expansion and Edge-Case Review

## Status

done

## Mode

implementation

## Goal

Pressure-test the 88T broker+shell-gate integration with expanded edge-case coverage, false-positive/negative review, mapping consistency checks, redaction checks, CLI JSON stability checks, and idle-vs-active task behavior tests. Fix only narrow classifier/broker integration defects found by those tests.

## Allowed Files

- src/pcae/core/permission_broker.py
- src/pcae/core/shell_gate.py
- src/pcae/commands/permission_broker.py
- tests/test_broker_shell_gate_integration.py
- tests/test_broker_shell_gate_edge_cases.py
- docs/PHASE_88_BROKER_SHELL_GATE_INTEGRATION_EDGE_CASE_REVIEW.md
- PROJECT_STATUS.md
- CHANGELOG.md
- pyproject.toml
- tasks/active/**
- tasks/DONE.md

## Forbidden Files

- TBD


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

- TBD

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-27T01:33:00.908905+02:00
