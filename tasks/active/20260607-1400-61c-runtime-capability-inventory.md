# Task Contract

## Task ID

20260607-1400-61c-runtime-capability-inventory

## Title

Runtime Capability Inventory (Phase 61C)

## Status

active

## Mode

implementation

## Goal

Implement pcae runtime-capability-inventory: 3 models (RuntimeCapability, RuntimeCapabilityInventoryAssessment, RuntimeCapabilityInventorySummary), 10 capability domains, inventory_allowed=False, registration_allowed=False, execution_allowed=False, human_review_required=True in Phase 61C.

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
- No runtime discovery on host
- No runtime registration
- No runtime configuration modification
- No repository modification

## Acceptance Checks

- pcae runtime-capability-inventory works
- pcae runtime-capability-inventory --json works
- RuntimeCapability implemented
- RuntimeCapabilityInventoryAssessment implemented
- RuntimeCapabilityInventorySummary implemented
- all capability domains defined
- inventory_allowed remains false
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
