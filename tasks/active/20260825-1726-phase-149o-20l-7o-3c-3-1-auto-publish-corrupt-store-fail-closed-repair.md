# Task Contract

## Task ID

20260825-1726-phase-149o-20l-7o-3c-3-1-auto-publish-corrupt-store-fail-closed-repair

## Title

Phase 149O.20L.7O.3C.3.1: Auto-Publish Corrupt-Store Fail-Closed Repair

## Status

active

## Mode

implementation

## Goal

Phase 149O.20L.7O.3C.3.1: Auto-Publish Corrupt-Store Fail-Closed Repair

## Allowed Files

- src/pcae/interactive_workflow/application/session_service.py
- src/pcae/commands/governance_auto_publication.py
- tests/test_phase_149o_20l_7o_3c_3_1_auto_publish_corrupt_store_fail_closed_repair.py
- tests/test_phase_149o_20l_7o_3c_3_independent_e2e_verification.py
- docs/PHASE_149O_20L_7O_3C_3_1_AUTO_PUBLISH_CORRUPT_STORE_FAIL_CLOSED_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**
- tasks/done/**
- .pcae/**

## Forbidden Files

- TBD

## Override Protected Files

- pyproject.toml


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

## Acceptance Criteria

- TBD

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-25T17:26:20.267191+02:00
