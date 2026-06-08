# Task Contract

## Task ID

20260608-1751-64b-1-capability-and-roadmap-intelligence

## Title

64B.1: Capability and Roadmap Intelligence

## Status

done

## Mode

implementation

## Goal

64B.1: Capability and Roadmap Intelligence

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
- src/pcae/core/docs.py
- tests/test_agent.py
- docs/COMMANDS.md
- docs/CAPABILITY_INVENTORY.md
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

2026-06-08T17:51:50.158839+02:00
