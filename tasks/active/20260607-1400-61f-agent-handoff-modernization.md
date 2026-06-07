# Task Contract

## Task ID

20260607-1400-61f-agent-handoff-modernization

## Title

Agent Handoff Modernization (Phase 61F)

## Status

active

## Mode

implementation

## Goal

Implement pcae agent-handoff-modernization: 3 models (AgentHandoffModernizationSignal, AgentHandoffModernizationAssessment, AgentHandoffModernizationSummary), 10 modernization domains, handoff_update_allowed=False, session_update_allowed=False, human_review_required=True in Phase 61F.

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
- No automatic handoff rewrite
- No task movement
- No session rewrite
- No repository modification by agents

## Acceptance Checks

- pcae agent-handoff-modernization works
- pcae agent-handoff-modernization --json works
- AgentHandoffModernizationSignal implemented
- AgentHandoffModernizationAssessment implemented
- AgentHandoffModernizationSummary implemented
- all modernization domains defined
- completed phase summary included
- active phase summary included
- next phase recommendation included
- roadmap position summary included
- runtime status summary included
- governance status summary included
- handoff_update_allowed remains false
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
