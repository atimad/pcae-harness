# Task: Phase 86E — Governance Event Timeline Extraction

## Objective

Implement a narrow read-only governance event timeline command that emits
ordered governance events as JSON to stdout. Extracts events from committed
artifacts, task files, git evidence, and the existing artifact index/memory
snapshot layer. No file writes, no cache, no .pcae storage, no authorization
inference.

## Allowed Files

- src/pcae/core/governance_timeline.py
- src/pcae/commands/governance_timeline.py
- src/pcae/cli.py
- tests/test_governance_timeline.py
- docs/PHASE_85_GOVERNANCE_TIMELINE_PROTOTYPE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/86e-read-only-governance-timeline-prototype.md
- tasks/completed/86d-read-only-memory-snapshot-prototype.md

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

## Acceptance Criteria

- pcae governance-timeline --json emits valid JSON
- Command is read-only (no file writes, no cache, no storage)
- Events are deterministic and ordered deterministically
- Event IDs are stable across repeated runs
- Tests added for JSON shape, safety flags, read-only behavior
- Existing pcae artifact-index --json still works
- Existing pcae memory-snapshot --json still works
- README.md unchanged

## Status

- [x] Created
- [x] In Progress
- [x] Complete
