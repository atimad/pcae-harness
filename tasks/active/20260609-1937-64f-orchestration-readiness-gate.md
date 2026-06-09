# Task Contract

## Task ID

20260609-1937-64f-orchestration-readiness-gate

## Title

64F Orchestration Readiness Gate

## Status

active

## Mode

implementation

## Goal

64F Orchestration Readiness Gate

## Allowed Files

- .pcae/session.json
- src/pcae/core/agent.py
- tests/test_agent.py
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- docs/CAPABILITY_INVENTORY.md
- docs/PROMPT_REGISTRY.md
- docs/SKILL_REGISTRY.md
- docs/ROADMAP_REGISTRY.md

## Forbidden Files

- TBD


## Allowed Zones

- TBD

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

strict

## Forbidden Changes

- No runtime invocation
- No prompt execution
- No source behavior changes outside 64F phase-state and prompt-governance transition work
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

2026-06-09T19:37:05.120202+02:00
