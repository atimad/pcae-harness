# Task: Phase 87C — Read-Only Gate Evaluation Dry-Run

## Objective

Implement a read-only dry-run gate evaluator that reports hypothetical gate
decisions as JSON to stdout. Does not enforce decisions, authorize actions,
invoke backends, or write storage/cache/state files.

## Allowed Files

- src/pcae/core/gate_dry_run.py
- src/pcae/commands/gate_dry_run.py
- src/pcae/cli.py
- tests/test_gate_dry_run.py
- docs/PHASE_87_GATE_DRY_RUN_PROTOTYPE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/87c-read-only-gate-dry-run-evaluator.md
- tasks/completed/87b-action-gate-taxonomy-decision-model.md

## Forbidden Files

- README.md
- docs/REAL_CAPTURED_TASKS.md
- .pcae/**
- existing design/prototype/integration/summary/verification artifacts
- docs/PHASE_87_GOVERNED_ACTION_GATES_PLAN.md
- docs/PHASE_87_ACTION_GATE_TAXONOMY_DECISION_MODEL.md

## Acceptance Criteria

- pcae gate-dry-run --json emits valid JSON
- 15 gates evaluated, all dry-run only
- No enforcement, no authorization, no storage
- Tests verify safety flags and no-write behavior
- Existing commands still work
- README.md unchanged

## Status

- [x] Created
- [x] In Progress
- [ ] Complete
