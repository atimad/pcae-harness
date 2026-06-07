# Task Contract

## Task ID

20260607-1400-61g-roadmap-continuity

## Title

Roadmap Continuity Validation (Phase 61G)

## Status

active

## Mode

implementation

## Goal

Implement pcae roadmap-continuity: 3 models (RoadmapContinuitySignal, RoadmapContinuityAssessment, RoadmapContinuitySummary), 10 continuity domains, roadmap_update_allowed=False, task_update_allowed=False, session_update_allowed=False, execution_allowed=False, human_review_required=True in Phase 61G.

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
- No automatic roadmap rewrite
- No automatic task completion
- No automatic task creation
- No session rewrite
- No repository modification by agents

## Acceptance Checks

- pcae roadmap-continuity works
- pcae roadmap-continuity --json works
- RoadmapContinuitySignal implemented
- RoadmapContinuityAssessment implemented
- RoadmapContinuitySummary implemented
- all continuity domains defined
- completed phase alignment included
- active phase alignment included
- next phase alignment included
- handoff roadmap alignment included
- pre-execution transition readiness included
- roadmap_update_allowed remains false
- task_update_allowed remains false
- session_update_allowed remains false
- execution_allowed remains false
- human review required
- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-07T14:00:00.000000+02:00
