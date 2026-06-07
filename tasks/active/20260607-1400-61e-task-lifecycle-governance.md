# Task Contract

## Task ID

20260607-1400-61e-task-lifecycle-governance

## Title

Task Lifecycle Governance Hardening (Phase 61E)

## Status

active

## Mode

implementation

## Goal

Implement pcae task-lifecycle-governance: 3 models (TaskLifecycleGovernanceSignal, TaskLifecycleGovernanceAssessment, TaskLifecycleGovernanceSummary), 8 governance domains, task_update_allowed=False, session_update_allowed=False, human_review_required=True in Phase 61E.

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

strict

## Forbidden Changes

- No runtime invocation
- No prompt execution
- No execution authorization
- No automatic task completion
- No automatic task creation
- No task movement
- No session rewrite
- No repository modification by agents

## Acceptance Checks

- pcae task-lifecycle-governance works
- pcae task-lifecycle-governance --json works
- TaskLifecycleGovernanceSignal implemented
- TaskLifecycleGovernanceAssessment implemented
- TaskLifecycleGovernanceSummary implemented
- all governance domains defined
- stale task contamination prevention included
- next task recommendation alignment included
- task_update_allowed remains false
- session_update_allowed remains false
- human review required
- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-07T14:00:00.000000+02:00
