# Task: Phase 86G — Risk Register Extraction

## Objective

Implement a narrow read-only risk register extraction command that emits risk
records as JSON to stdout. Extracts risks from committed artifacts, task files,
governance timeline, decision log, git evidence, and existing layers. No file
writes, no cache, no .pcae storage, no authorization inference.

## Allowed Files

- src/pcae/core/risk_register.py
- src/pcae/commands/risk_register.py
- src/pcae/cli.py
- tests/test_risk_register.py
- docs/PHASE_85_RISK_REGISTER_PROTOTYPE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/86g-read-only-risk-register-prototype.md
- tasks/completed/86f-read-only-decision-log-prototype.md

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

## Acceptance Criteria

- pcae risk-register --json emits valid JSON
- Command is read-only (no file writes, no cache, no storage)
- Risks are deterministic and ordered deterministically
- Risk IDs are stable across repeated runs
- Accepted risk is not treated as mitigated risk
- Stale signal risks remain visible
- Must-never-repeat risks remain visible
- Tests added for JSON shape, safety flags, read-only behavior
- Existing commands still work
- README.md unchanged

## Status

- [x] Created
- [x] In Progress
- [ ] Complete
