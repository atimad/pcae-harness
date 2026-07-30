# Task Contract

## Task ID

20260730-2124-phase-147g-authority-evaluation-model-core-implementation

## Title

Phase 147G: Authority Evaluation Model Core Implementation

## Status

done

## Mode

implementation

## Goal

Implement the standalone pcae.authority_evaluation package per AEMIC-001 v1.2: models.py, evaluation.py, registry.py (ABC only), errors.py, serialization.py, __init__.py. No concrete Registry, no lifecycle/runtime/publication integration. Comprehensive production tests. Produce implementation report and requirement/test coverage matrix.

## Allowed Files

- src/pcae/authority_evaluation/**
- tests/test_phase_147g_*.py
- docs/PHASE_147G_AUTHORITY_EVALUATION_MODEL_CORE_IMPLEMENTATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/TODO.md
- .pcae/policy.toml
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/active/20260730-2105-idle-awaiting-next-governed-phase-post-147f-2.md
- tasks/done/20260730-2105-idle-awaiting-next-governed-phase-post-147f-2.md

## Forbidden Files

- TBD


## Allowed Zones

- authority_evaluation
- tests
- docs
- tasks
- policy
- config

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

- src/pcae/authority_evaluation/ package exists with exactly the six required modules
- No concrete Registry implementation exists in registry.py
- No forbidden import from interactive_workflow, governance, cltr, commands, cli, core, lifecycle, or repository_intelligence
- Every AEMIC-001 v1.2 requirement maps to at least one executable test
- Disclosure-only semantics preserved; no authorize/grant/permit/deny naming
- Runtime remains Observed/observe/unavailable; no lifecycle/publication/CLI integration
- Full existing test suite passes unchanged (no regression)

## Acceptance Checks

- pcae health
- pcae check
- pcae doctor task-memory
- python -m pytest -m fast_green -n auto

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-30T21:24:10.123100+02:00
