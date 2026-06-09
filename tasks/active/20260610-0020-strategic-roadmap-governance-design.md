# Task Contract

## Task ID

20260610-0020-strategic-roadmap-governance-design

## Title

Strategic Roadmap Governance Design

## Status

active

## Mode

implementation

## Goal

Implement Phase 65A: introduce a strategic governance layer above the roadmap. Add project goal, vision, objective, branch, capability-objective map, recommendation, evolution proposal, branch health, and human approval models. All advisory-only; no auto-mutation of existing registries. Export STRATEGIC_ROADMAP_GOVERNANCE_ADVISORY. ~20 tests across 10 validation domains.

## Allowed Files

- src/pcae/core/agent.py
- tests/test_agent.py
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/20260610-0020-strategic-roadmap-governance-design.md
- tasks/done/20260609-2231-64g-capability-inventory-alignment-hardening.md
- .pcae/session.json

## Allowed Zones

- core
- tests
- docs
- tasks
- session
- config

## Forbidden Files

- TBD

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

advisory

## Forbidden Changes

- No runtime invocation
- No execution_allowed = True
- No auto-modification of _CRI_KNOWN_PHASES or _CRI_KNOWN_CAPABILITIES by new code
- No task lifecycle changes outside task commands

## Acceptance Checks

- build_strategic_roadmap_governance() returns valid dict with all top-level keys
- governance_boundaries["execution_allowed"] == False
- All 4842+ tests pass
- pcae check passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-10T00:20:03.535724+02:00
