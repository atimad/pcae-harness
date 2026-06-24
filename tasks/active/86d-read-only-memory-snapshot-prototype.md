# Task: Phase 86D — Persistent Memory Snapshot Prototype

## Objective

Implement a narrow read-only memory snapshot command that emits a JSON memory
snapshot to stdout. Reuses the artifact index internally. No file writes,
no cache, no .pcae storage, no authorization inference.

## Allowed Files

- src/pcae/core/memory_snapshot.py
- src/pcae/commands/memory_snapshot.py
- src/pcae/cli.py
- tests/test_memory_snapshot.py
- docs/PHASE_85_MEMORY_SNAPSHOT_PROTOTYPE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/86d-read-only-memory-snapshot-prototype.md
- tasks/completed/86c-read-only-artifact-index-prototype.md

## Forbidden Files

- README.md
- docs/REAL_CAPTURED_TASKS.md
- .pcae/**
- .githooks/**
- existing Phase 85 design docs
- docs/PHASE_85_IMPLEMENTATION_ROADMAP.md
- docs/PHASE_85_DATA_MODEL_STORAGE_DESIGN.md
- docs/PHASE_85_ARTIFACT_INDEX_PROTOTYPE.md

## Acceptance Criteria

- pcae memory-snapshot --json emits valid JSON
- Command is read-only (no file writes, no cache, no storage)
- Tests added for JSON shape, safety flags, read-only behavior
- Existing pcae artifact-index --json still works
- README.md unchanged

## Status

- [x] Created
- [x] In Progress
- [x] Complete
