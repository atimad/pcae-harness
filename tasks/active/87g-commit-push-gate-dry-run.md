# Task: Phase 87G — Commit and Push Gate Dry-Run

## Objective

Implement narrow read-only dry-run evaluation for commit and push gates.
Evaluates proposed commit/push without staging, committing, pushing, or
writing storage.

## Allowed Files

- src/pcae/core/gate_dry_run.py
- src/pcae/commands/gate_dry_run.py
- src/pcae/cli.py
- tests/test_commit_push_gate.py
- docs/PHASE_87_COMMIT_PUSH_GATE_DRY_RUN.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/87g-commit-push-gate-dry-run.md
- tasks/completed/87f-adoption-mutation-gate-dry-run.md

## Forbidden Files

- README.md
- docs/REAL_CAPTURED_TASKS.md
- .pcae/**
- existing design/prototype/integration/summary/verification artifacts
- All 87A-87F artifacts

## Acceptance Criteria

- Commit/push gates evaluate requests without staging/committing/pushing
- authorization_granted=false for every gate
- No staging/commit/push during gate command execution
- Tests verify non-commit and non-push
- Existing commands still work
- README.md unchanged

## Status

- [x] Created
- [x] In Progress
- [x] Complete
