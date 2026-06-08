# Task Contract

## Task ID

20260608-2134-64b-5-skill-invocation-targeting

## Title

64B.5: Skill Invocation Targeting

## Status

done

## Mode

implementation

## Goal

64B.5: Skill Invocation Targeting

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
- src/pcae/commands/agent.py
- src/pcae/cli.py
- tests/test_agent.py
- docs/SKILL_REGISTRY.md
- docs/COMMANDS.md
- docs/ROADMAP_REGISTRY.md
- docs/CAPABILITY_INVENTORY.md

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

2026-06-08T21:34:55.497191+02:00
