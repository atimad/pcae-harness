# Task: Phase 88B — Scope Gate Preflight Prototype

## Objective

Implement the first narrow scope gate preflight prototype. Add an explicit
command that evaluates whether a requested action and requested files are
permitted by the active task contract scope. The command returns structured
JSON with a preflight decision, reason codes, scope matches, evidence, and
safety notes.

## Allowed Files

- src/pcae/core/scope_preflight.py
- src/pcae/commands/scope_preflight.py
- src/pcae/cli.py
- src/pcae/core/docs.py
- tests/test_scope_preflight.py
- docs/PHASE_88_SCOPE_GATE_PREFLIGHT_PROTOTYPE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/88b-scope-gate-preflight-prototype.md
- tasks/completed/88a-first-enforced-gate-boundary.md
- docs/COMMANDS.md

## Forbidden Files

- README.md
- docs/LINKEDIN_ARTICLE_DRAFT.md
- docs/REAL_CAPTURED_TASKS.md
- docs/PHASE_88_FIRST_ENFORCED_GATE_BOUNDARY.md
- .pcae/**
- .githooks/**

## Acceptance Criteria

- Explicit scope preflight command exists
- Command supports JSON output
- Command accepts requested action and one or more requested files
- Command reads active task contract
- Command reports preflight decision with reason codes
- Command reports safety notes
- authorization_granted=false
- execution_authorized=false
- repo_mutation_performed=false
- storage_written=false
- backend_invocation_performed=false
- Existing pcae gate-dry-run --json still works
- Existing read-only commands still work
- New scope preflight tests pass
- docs/PHASE_88_SCOPE_GATE_PREFLIGHT_PROTOTYPE.md exists
- README.md unchanged
- No permission broker, shell gate, or broad enforcement

## Status

- [x] Created
- [x] In Progress
- [ ] Complete
