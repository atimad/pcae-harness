# Task Contract

## Task ID

20260612-1032-67a-comparative-irg-challenge-architecture

## Title

67A Comparative IRG Challenge Architecture

## Status

done

## Mode

implementation

## Goal

67A Comparative IRG Challenge Architecture

## Allowed Files

- .pcae/session.json
- .pcae/strategic-lineage.json
- .pcae/provenance-history.json
- src/pcae/cli.py
- src/pcae/commands/agent.py
- src/pcae/commands/phase.py
- src/pcae/commands/session.py
- src/pcae/core/agent.py
- src/pcae/core/docs.py
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- docs/COMMANDS.md
- docs/CAPABILITY_INVENTORY.md
- docs/ROADMAP_REGISTRY.md
- tests/test_agent.py
- tests/test_phase.py
- tests/test_session.py
- tests/test_docs.py
- tests/test_strategic_lineage.py

## Forbidden Files

- TBD


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

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

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

2026-06-12T10:32:36.235831+02:00
