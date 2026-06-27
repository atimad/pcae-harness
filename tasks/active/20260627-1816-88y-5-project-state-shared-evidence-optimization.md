# Task Contract

## Task ID

20260627-1816-88y-5-project-state-shared-evidence-optimization

## Title

88Y.5 — Project State Shared Evidence Optimization

## Status

active

## Mode

implementation

## Goal

Optimize build_project_state() internal cascade using per-invocation shared evidence, no persistent cache, no global cache, no decision changes

## Allowed Files

- src/pcae/core/project_state.py
- src/pcae/core/gate_dry_run_context.py
- src/pcae/core/gate_dry_run.py
- src/pcae/core/memory_snapshot.py
- src/pcae/core/governance_timeline.py
- src/pcae/core/decision_log.py
- src/pcae/core/risk_register.py
- tests/test_gate_dry_run_context.py
- tests/test_gate_dry_run.py
- tests/test_phase87_integration.py
- tests/test_project_state_context.py
- docs/PHASE_88_PROJECT_STATE_SHARED_EVIDENCE_OPTIMIZATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/20260627-1816-88y-5-project-state-shared-evidence-optimization.md
- tasks/active/**

## Forbidden Files

- README.md
- docs/LINKEDIN_ARTICLE_DRAFT.md
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

TBD

## Forbidden Changes

- TBD

## Acceptance Criteria

- build_project_state() cascade analyzed
- Behavior-preserving optimization implemented or bottleneck documented
- No persistent cache, no global cache, no cross-invocation cache
- Decision-equivalence tests added or preserved
- Gate decisions unchanged
- All test tiers green

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-27T18:16:38.440251+02:00
