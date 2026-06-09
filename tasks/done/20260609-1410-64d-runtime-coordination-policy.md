# Task Contract

## Task ID

20260609-1410-64d-runtime-coordination-policy

## Title

64D Runtime Coordination Policy

## Status

done

## Mode

implementation

## Goal

64D Runtime Coordination Policy

## Allowed Files

- .pcae/session.json
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- src/pcae/core/agent.py
- tests/test_agent.py
- docs/CAPABILITY_INVENTORY.md
- docs/ROADMAP_REGISTRY.md
- docs/PROMPT_REGISTRY.md
- docs/SKILL_REGISTRY.md

## Forbidden Files

- src/pcae/commands/**
- src/pcae/cli.py


## Allowed Zones

- core
- tests
- tasks
- docs
- session
- config

## Forbidden Zones

- TBD

## Allowed Dependencies

- core -> core
- core -> tests
- tests -> core
- tests -> commands
- tests -> cli

## Forbidden Dependencies

- TBD

## Enforcement Mode

strict

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

2026-06-09T14:10:02.083301+02:00
