# Task Contract

## Task ID

20260607-1400-61a-runtime-registry

## Title

Runtime Registry (Phase 61A)

## Status

active

## Mode

implementation

## Goal

Implement pcae runtime-registry: 4 models (RuntimeRegistrySignal, RuntimeRegistryEntry, RuntimeRegistryAssessment, RuntimeRegistrySummary), 8 registry domains, registration_allowed=False, execution_allowed=False, human_review_required=True in Phase 61A.

## Allowed Files

- .pcae/session.json
- tasks/active/**
- tasks/done/**
- CHANGELOG.md
- PROJECT_STATUS.md
- docs/COMMANDS.md
- src/pcae/cli.py
- src/pcae/commands/agent.py
- src/pcae/core/agent.py
- src/pcae/core/docs.py
- tests/test_agent.py

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

- No runtime invocation
- No prompt execution
- No execution authorization
- No runtime discovery
- No runtime registration
- No runtime configuration modification
- No repository modification

## Acceptance Checks

- pcae runtime-registry works
- pcae runtime-registry --json works
- RuntimeRegistrySignal implemented
- RuntimeRegistryEntry implemented
- RuntimeRegistryAssessment implemented
- RuntimeRegistrySummary implemented
- all registry domains defined
- trust levels defined
- runtime statuses defined
- registration_allowed remains false
- execution_allowed remains false
- human review required
- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-07T14:00:00.000000+02:00
