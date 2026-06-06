# Task Contract

## Task ID

20260605-1052-multi-agent-governance-audit

## Title

Multi-agent governance audit

## Status

done

## Mode

implementation

## Goal

Implement Phase 52M only: a read-only, advisory conflict resolution engine
scaffold for multi-agent and concurrent PCAE workflows.

## Allowed Files

- .pcae/session.json
- tasks/active/**
- tasks/done/**
- CHANGELOG.md
- PROJECT_STATUS.md
- docs/COMMANDS.md
- src/pcae/cli.py
- src/pcae/commands/agent.py
- src/pcae/core/agent.py
- src/pcae/core/docs.py
- tests/test_agent.py

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

TBD

## Forbidden Changes

- Runtime invocation or prompt execution.
- Execution authorization.
- Automatic conflict resolution.
- Lock, task, session, governance, runtime, or evidence mutation.
- Commit, push, or rollback.

## Acceptance Checks

- `pcae conflict-resolution-engine` works.
- `pcae conflict-resolution-engine --json` works.
- Conflict signal, assessment, and summary models are defined.
- All eight conflict resolution domains are represented.
- Resolution remains advisory and execution remains blocked.
- `pcae check` passes.
- `python -m pytest -n auto` passes.

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-05T10:52:21.508406+02:00
