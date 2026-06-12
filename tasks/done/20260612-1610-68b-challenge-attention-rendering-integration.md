# Task Contract

## Task ID

20260612-1610-68b-challenge-attention-rendering-integration

## Title

68B Challenge Attention Rendering Integration

## Status

done

## Mode

implementation

## Goal

Wire the 68A attention allocator into the automatic challenge rendering path (session bootstrap, phase handoff, phase completion). Explicit pcae irg-challenge command retains full-detail display. JSON output retains all findings. Allocator changes visibility only — no governance outcomes, no finding mutations, no command exit code changes.

## Allowed Files

- .pcae/session.json
- .pcae/strategic-lineage.json
- .pcae/provenance-history.json
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- src/pcae/core/agent.py
- src/pcae/core/docs.py
- src/pcae/commands/agent.py
- src/pcae/commands/session.py
- src/pcae/commands/phase.py
- src/pcae/cli.py
- tests/test_agent.py
- tests/test_strategic_lineage.py
- docs/COMMANDS.md
- docs/CAPABILITY_INVENTORY.md
- docs/ROADMAP_REGISTRY.md

## Forbidden Files

- none

## Allowed Zones

## Forbidden Zones

## Allowed Dependencies

## Forbidden Dependencies


## Enforcement Mode

advisory

## Forbidden Changes

- No change to finding generation logic
- No change to challenge rule logic
- No change to challenge comparison logic
- No change to governance outcomes (health, check, readiness, approvals, task transition)
- No change to command exit codes
- No runtime invocation
- No prompt execution
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

2026-06-12T16:10:49.474848+02:00
