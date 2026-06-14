# Task Contract

## Task ID

20260613-0849-69c-invocation-contract-validation

## Title

69C Invocation Contract Validation

## Status

done

## Mode

implementation

## Goal

69C Invocation Contract Validation

## Allowed Files

- .pcae/session.json
- .pcae/agent-lock.json
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
- src/pcae/commands/agent.py
- src/pcae/cli.py
- tests/test_agent.py
- tests/test_strategic_lineage.py
- docs/COMMANDS.md
- src/pcae/core/docs.py
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

advisory

## Forbidden Changes

- No runtime invocation
- No prompt execution
- No execution authorization (execution_allowed=False invariant)
- No real execution activation
- No write authorization activation
- No multi-runtime routing expansion beyond codex-local and claude-local contract verification
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

2026-06-13T08:49:36+02:00
