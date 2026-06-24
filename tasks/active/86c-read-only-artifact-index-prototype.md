# Task: Phase 86C — Read-Only Artifact Index Prototype

## Objective

Implement a narrow read-only artifact index prototype that scans known committed
repository artifacts and emits JSON artifact records to stdout. No file writes,
no cache, no .pcae storage, no backend invocation, no authorization.

## Allowed Files

- src/pcae/core/artifact_index.py
- src/pcae/commands/artifact_index.py
- src/pcae/cli.py
- tests/test_artifact_index.py
- docs/PHASE_85_ARTIFACT_INDEX_PROTOTYPE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/86c-read-only-artifact-index-prototype.md
- tasks/completed/86b-phase-85-data-model-storage-design.md

## Forbidden Files

- README.md
- docs/REAL_CAPTURED_TASKS.md
- .pcae/**
- .githooks/**
- existing Phase 85 design docs
- docs/PHASE_85_IMPLEMENTATION_ROADMAP.md
- docs/PHASE_85_DATA_MODEL_STORAGE_DESIGN.md

## Acceptance Criteria

- pcae artifact-index --json emits valid JSON
- Command is read-only (no file writes, no cache, no storage)
- Tests added for JSON shape, safety flags, read-only behavior
- Source code unchanged except new command module
- README.md unchanged

## Status

- [x] Created
- [x] In Progress
- [x] Complete
