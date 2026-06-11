# Task Contract

## Task ID

20260611-1300-65i-strategic-registry-coherence-hardening

## Title

65I Strategic Registry Coherence Hardening

## Status

active

## Mode

implementation

## Goal

Implement Phase 65I: Strategic Registry Coherence Hardening. Detect blocking strategic registry defects without mutating state, classify CRI/CI projection differences explicitly, surface generated artifact drift separately from authoritative registry corruption, and integrate blocking coherence failures into `pcae status coherence`, `pcae check`, and `pcae health`.

## Allowed Files

- .pcae/session.json
- tasks/active/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- docs/ROADMAP_REGISTRY.md
- docs/CAPABILITY_INVENTORY.md
- docs/COMMANDS.md
- src/pcae/core/agent.py
- src/pcae/core/status.py
- src/pcae/core/check.py
- src/pcae/core/health.py
- src/pcae/core/architecture.py
- src/pcae/core/export.py
- src/pcae/commands/agent.py
- src/pcae/commands/check.py
- src/pcae/commands/status.py
- src/pcae/commands/session.py
- src/pcae/commands/phase.py
- tests/test_agent.py
- tests/test_architecture.py
- tests/test_check.py
- tests/test_export.py
- tests/test_health.py
- tests/test_phase.py
- tests/test_session.py
- tests/test_status.py

## Forbidden Files

## Allowed Zones

## Forbidden Zones

## Allowed Dependencies

## Forbidden Dependencies

## Enforcement Mode

advisory

## Forbidden Changes

- No runtime execution
- No prompt execution
- No write execution inside validation commands
- No automatic roadmap or branch-registry mutation from validation flows
- No auto-regeneration of docs from validation flows
- No commit
- No push
- No rollback

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files for roadmap, task, and workflow-visible changes.

## Created Timestamp

2026-06-11T13:00:00+02:00
