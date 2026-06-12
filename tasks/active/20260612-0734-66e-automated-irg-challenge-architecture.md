# Task Contract

## Task ID

20260612-0734-66e-automated-irg-challenge-architecture

## Title

66E Automated IRG Challenge Architecture

## Status

active

## Mode

implementation

## Goal

66E Automated IRG Challenge Architecture

## Allowed Files

- .pcae/session.json
- .pcae/strategic-lineage.json
- .pcae/provenance-history.json
- src/pcae/cli.py
- src/pcae/commands/agent.py
- src/pcae/commands/phase.py
- src/pcae/commands/session.py
- src/pcae/core/agent.py
- src/pcae/core/context.py
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
- tests/test_context.py
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
- No source behavior changes outside approved advisory challenge display surfaces and explicit irg-challenge command plumbing
- No execution authorization
- No commit
- No push
- No rollback
- No pcae check integration
- No pre-commit integration
- No task transition gating
- No phase activation integration
- No lineage creation integration
- No roadmap mutation integration
- No persistence by default
- No acknowledgement workflow
- No override workflow
- No remediation workflow
- No approval/rejection/recommendation semantics in challenge output
- No required_changes output
- No exit-code, readiness-state, approval-state, bootstrap-state, handoff-state, or completion-state changes from challenge findings

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-12T07:34:03.517473+02:00
