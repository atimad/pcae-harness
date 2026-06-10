# Task Contract

## Task ID

20260610-0706-strategic-state-summary

## Title

Strategic State Summary

## Status

active

## Mode

implementation

## Goal

Implement Phase 65B: add Strategic State Summary capability. Compute objective coverage governance, detect unmapped capabilities (warning-level severity by default), generate mapping recommendations with evidence, and produce evidence-based reports. All advisory-only; no auto-mutation of existing registries. Export STRATEGIC_STATE_SUMMARY_ADVISORY. ~22 tests across 10 validation domains.

## Allowed Files

- src/pcae/core/agent.py
- tests/test_agent.py
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/20260610-0706-strategic-state-summary.md
- tasks/done/20260610-0020-strategic-roadmap-governance-design.md
- .pcae/session.json

## Forbidden Files

- TBD

## Allowed Zones

- core
- tests
- docs
- tasks
- session
- config

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
- No auto-application of mapping recommendations
- No roadmap mutation
- No task lifecycle changes outside task commands

## Acceptance Checks

- build_strategic_state_summary() returns valid dict with all top-level keys
- governance_boundaries["execution_allowed"] == False
- governance_boundaries["auto_apply_capability_mappings"] == False
- unmapped capabilities produce warning-level signals by default
- objective_coverage_status and mapping_completeness_status computed independently
- All 4862+ tests pass
- pcae check passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-10T07:06:15.960342+02:00
