# Task Contract

## Task ID

20260626-1706-88r-permission-broker-prototype

## Title

88R Permission Broker Prototype

## Status

done

## Mode

implementation

## Goal

Implement first permission broker prototype as read-only decision aggregator consuming PCAE governance evidence

## Allowed Files

- src/pcae/core/permission_broker.py
- src/pcae/commands/permission_broker.py
- src/pcae/cli.py
- tests/test_permission_broker.py
- tests/conftest.py
- docs/PHASE_88_PERMISSION_BROKER_PROTOTYPE.md
- PROJECT_STATUS.md
- CHANGELOG.md
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

strict

## Forbidden Changes

- TBD

## Acceptance Criteria

- TBD

## Acceptance Checks

- python -m pytest tests/test_permission_broker.py -q
- python -m pytest -m fast_green -n auto -q

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-26T17:06:29.383433+02:00
