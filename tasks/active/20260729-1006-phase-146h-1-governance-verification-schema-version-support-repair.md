# Task Contract

## Task ID

20260729-1006-phase-146h-1-governance-verification-schema-version-support-repair

## Title

Phase 146H.1: Governance Verification Schema-Version Support Repair

## Status

active

## Mode

read_write

## Goal

Phase 146H.1: Governance Verification Schema-Version Support Repair

## Allowed Files

- src/pcae/governance/verification.py
- tests/fixtures/chgr/**
- tests/test_phase_146h1_governance_verification_schema_version_repair.py
- docs/PHASE_146H1_*.md
- docs/PHASE_146H_CHGR001_SCHEMA_ENVELOPE_INDEPENDENT_IMPLEMENTATION_VERIFICATION.md
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md

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

2026-07-29T10:06:05.523895+02:00
