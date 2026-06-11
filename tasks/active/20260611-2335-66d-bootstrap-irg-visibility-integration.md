# Task Contract

## Task ID

20260611-2335-66d-bootstrap-irg-visibility-integration

## Title

66D Bootstrap IRG Visibility Integration

## Status

active

## Mode

implementation

## Goal

66D Bootstrap IRG Visibility Integration

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
- src/pcae/core/context.py
- src/pcae/core/docs.py
- src/pcae/core/strategic_lineage.py
- tests/test_agent.py
- tests/test_context.py
- tests/test_strategic_lineage.py
- docs/CAPABILITY_INVENTORY.md
- docs/ROADMAP_REGISTRY.md

## Forbidden Files

- .pcae/irg-review-records.json
- .pcae/irg-overrides.json

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
- No pcae check integration (rejected for 66D)
- No task transition integration (rejected for 66D)
- No phase handoff integration (rejected for 66D)
- No provenance event for review surfacing (rejected for 66D)
- No new review or override registries (rejected for 66D)
- No stale-review enforcement, artifact hashing, or review gates (rejected for 66D)
- No blocking behavior from review findings (review_blocks_any_operation=False)
- Strategic-lineage validator changes are limited to preserving immutable historical approved records and restricting branch current_phase matching to the current non-superseded active lineage record.

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-11T23:35:19.638647+02:00
