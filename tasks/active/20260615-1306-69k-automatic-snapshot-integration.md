# Task Contract

## Task ID

20260615-1306-69k-automatic-snapshot-integration

## Title

69K Automatic Snapshot Integration

## Status

active

## Mode

implementation

## Goal

69K Automatic Snapshot Integration

## Allowed Files

- .pcae/session.json
- .pcae/strategic-lineage.json
- .pcae/provenance-history.json
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- src/pcae/core/agent.py
- src/pcae/commands/agent.py
- src/pcae/cli.py
- src/pcae/core/docs.py
- tests/test_agent.py
- tests/test_strategic_lineage.py
- docs/COMMANDS.md
- docs/CAPABILITY_INVENTORY.md
- docs/ROADMAP_REGISTRY.md

## Forbidden Files

- src/pcae/core/strategic_lineage.py

## Allowed Zones

- core
- commands
- cli
- tests
- docs
- tasks
- session
- config

## Forbidden Zones

## Allowed Dependencies

## Forbidden Dependencies

## Enforcement Mode

advisory

## Forbidden Changes

- No runtime invocation
- No prompt execution
- No source behavior changes outside task/session/handoff governance
- No execution authorization
- No commit
- No push
- No rollback

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-15T13:06:24.782077+02:00
