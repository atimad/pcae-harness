# Task: Phase 86F — Decision Log Extraction

## Objective

Implement a narrow read-only decision log extraction command that emits decision
records as JSON to stdout. Extracts decisions from committed artifacts, task files,
governance timeline, git evidence, and existing artifact/memory/timeline layers.
No file writes, no cache, no .pcae storage, no authorization inference.

## Allowed Files

- src/pcae/core/decision_log.py
- src/pcae/commands/decision_log.py
- src/pcae/cli.py
- tests/test_decision_log.py
- docs/PHASE_85_DECISION_LOG_PROTOTYPE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/86f-read-only-decision-log-prototype.md
- tasks/completed/86e-read-only-governance-timeline-prototype.md

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

## Acceptance Criteria

- pcae decision-log --json emits valid JSON
- Command is read-only (no file writes, no cache, no storage)
- Decisions are deterministic and ordered deterministically
- Decision IDs are stable across repeated runs
- Authorization flags are explicit; high-risk flags remain false
- Tests added for JSON shape, safety flags, read-only behavior
- Existing pcae artifact-index --json still works
- Existing pcae memory-snapshot --json still works
- Existing pcae governance-timeline --json still works
- README.md unchanged

## Status

- [x] Created
- [x] In Progress
- [x] Complete
