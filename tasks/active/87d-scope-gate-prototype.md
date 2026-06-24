# Task: Phase 87D — Scope Gate Prototype

## Objective

Implement a narrow read-only scope gate prototype inside the existing gate
dry-run evaluator. Evaluates file/action scope using task contract evidence.
Dry-run only. No enforcement, no authorization, no storage.

## Allowed Files

- src/pcae/core/gate_dry_run.py
- src/pcae/commands/gate_dry_run.py
- src/pcae/cli.py
- tests/test_gate_dry_run.py
- tests/test_scope_gate.py
- docs/PHASE_87_SCOPE_GATE_PROTOTYPE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/87d-scope-gate-prototype.md
- tasks/completed/87c-read-only-gate-dry-run-evaluator.md

## Forbidden Files

- README.md
- docs/REAL_CAPTURED_TASKS.md
- .pcae/**
- existing design/prototype/integration/summary/verification artifacts
- docs/PHASE_87_GOVERNED_ACTION_GATES_PLAN.md
- docs/PHASE_87_ACTION_GATE_TAXONOMY_DECISION_MODEL.md
- docs/PHASE_87_GATE_DRY_RUN_PROTOTYPE.md

## Acceptance Criteria

- Scope gate evaluates requested files against task contract
- Optional --requested-action and --requested-file flags
- Default command still works
- gate_count remains 15
- No enforcement, no authorization, no storage
- README.md unchanged

## Status

- [x] Created
- [x] In Progress
- [x] Complete
