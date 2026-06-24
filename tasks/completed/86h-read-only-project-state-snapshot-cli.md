# Task: Phase 86H — Project State Snapshot CLI

## Objective

Implement a narrow read-only project state snapshot command that emits a
project-state snapshot as JSON to stdout. Aggregates artifact index, memory
snapshot, governance timeline, decision log, and risk register into one
current project-state answer surface. No file writes, no cache, no .pcae
storage, no authorization inference.

## Allowed Files

- src/pcae/core/project_state.py
- src/pcae/commands/project_state.py
- src/pcae/cli.py
- tests/test_project_state.py
- docs/PHASE_85_PROJECT_STATE_SNAPSHOT_PROTOTYPE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/86h-read-only-project-state-snapshot-cli.md
- tasks/completed/86g-read-only-risk-register-prototype.md

## Forbidden Files

- README.md
- docs/REAL_CAPTURED_TASKS.md
- .pcae/**
- .githooks/**
- existing Phase 85 design docs
- docs/PHASE_85_IMPLEMENTATION_ROADMAP.md
- docs/PHASE_85_DATA_MODEL_STORAGE_DESIGN.md
- docs/PHASE_85_ARTIFACT_INDEX_PROTOTYPE.md
- docs/PHASE_85_MEMORY_SNAPSHOT_PROTOTYPE.md
- docs/PHASE_85_GOVERNANCE_TIMELINE_PROTOTYPE.md
- docs/PHASE_85_DECISION_LOG_PROTOTYPE.md
- docs/PHASE_85_RISK_REGISTER_PROTOTYPE.md

## Acceptance Criteria

- pcae project-state --json emits valid JSON
- Command is read-only (no file writes, no cache, no storage)
- Snapshot integrates all five read-only layers
- Authorization booleans explicit; high-risk flags false
- Next safe actions are recommendations, not authorizations
- Accepted risks and stale signals remain visible
- Tests added for JSON shape, safety flags, read-only behavior
- Existing commands still work
- README.md unchanged

## Status

- [x] Created
- [x] In Progress
- [x] Complete
