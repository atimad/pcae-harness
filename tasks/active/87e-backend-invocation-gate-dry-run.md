# Task: Phase 87E — Backend Invocation Gate Dry-Run

## Objective

Implement a narrow read-only backend invocation gate dry-run inside the
existing gate dry-run evaluator. Evaluates proposed backend invocation
without invoking backends, sending prompts, or capturing output.

## Allowed Files

- src/pcae/core/gate_dry_run.py
- src/pcae/commands/gate_dry_run.py
- src/pcae/cli.py
- tests/test_backend_gate.py
- docs/PHASE_87_BACKEND_INVOCATION_GATE_DRY_RUN.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/87e-backend-invocation-gate-dry-run.md
- tasks/completed/87d-scope-gate-prototype.md

## Forbidden Files

- README.md
- docs/REAL_CAPTURED_TASKS.md
- .pcae/**
- existing design/prototype/integration/summary/verification artifacts
- docs/PHASE_87_GOVERNED_ACTION_GATES_PLAN.md
- docs/PHASE_87_ACTION_GATE_TAXONOMY_DECISION_MODEL.md
- docs/PHASE_87_GATE_DRY_RUN_PROTOTYPE.md
- docs/PHASE_87_SCOPE_GATE_PROTOTYPE.md

## Acceptance Criteria

- Backend invocation gate evaluates requested backends
- No backend invoked, no prompt sent, no output captured
- authorization_granted=false for every gate
- Tests verify no-invocation and non-authorization
- Existing commands still work
- README.md unchanged

## Status

- [x] Created
- [x] In Progress
- [ ] Complete
