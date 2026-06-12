# Task Contract

## Task ID

20260612-1731-persistent-attention-rebalancing-architecture

## Title

Persistent Attention Rebalancing Architecture

## Status

done

## Mode

implementation

## Goal

Persistent Attention Rebalancing Architecture

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
- src/pcae/core/docs.py
- src/pcae/commands/agent.py
- src/pcae/commands/session.py
- src/pcae/commands/phase.py
- src/pcae/cli.py
- tests/test_agent.py
- tests/test_strategic_lineage.py
- docs/COMMANDS.md
- docs/CAPABILITY_INVENTORY.md
- docs/ROADMAP_REGISTRY.md

## Forbidden Files

- none

## Allowed Zones

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

2026-06-12T17:31:22.933163+02:00
