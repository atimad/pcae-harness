# Task: Phase 87F — Adoption and Mutation Gate Dry-Run

## Objective

Implement narrow read-only dry-run evaluation for adoption and mutation gates.
Evaluates proposed adoption/mutation without performing intake, review, approval,
execution, file mutation, or storage writes.

## Allowed Files

- src/pcae/core/gate_dry_run.py
- src/pcae/commands/gate_dry_run.py
- src/pcae/cli.py
- tests/test_adoption_mutation_gate.py
- docs/PHASE_87_ADOPTION_MUTATION_GATE_DRY_RUN.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/87f-adoption-mutation-gate-dry-run.md
- tasks/completed/87e-backend-invocation-gate-dry-run.md

## Forbidden Files

- README.md
- docs/REAL_CAPTURED_TASKS.md
- .pcae/**
- existing design/prototype/integration/summary/verification artifacts
- docs/PHASE_87_GOVERNED_ACTION_GATES_PLAN.md
- docs/PHASE_87_ACTION_GATE_TAXONOMY_DECISION_MODEL.md
- docs/PHASE_87_GATE_DRY_RUN_PROTOTYPE.md
- docs/PHASE_87_SCOPE_GATE_PROTOTYPE.md
- docs/PHASE_87_BACKEND_INVOCATION_GATE_DRY_RUN.md

## Acceptance Criteria

- Adoption/mutation gates evaluate requests without performing adoption/mutation
- authorization_granted=false for every gate
- No intake/review/approval/execution/mutation performed
- Tests verify non-adoption and non-mutation
- Existing commands still work
- README.md unchanged

## Status

- [x] Created
- [x] In Progress
- [ ] Complete
