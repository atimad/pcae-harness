# Task Contract

## Task ID

20260804-2000-phase-149n-rollback-approval-evidence-canonical-provenance-hardening

## Title

Phase 149N: Rollback Approval Evidence Canonical-Provenance Hardening

## Status

active

## Mode

implementation

## Goal

Phase 149N: Rollback Approval Evidence Canonical-Provenance Hardening

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- src/pcae/core/rollback_approval_evidence.py
- docs/PHASE_149N_ROLLBACK_APPROVAL_EVIDENCE_CANONICAL_PROVENANCE_HARDENING.md
- tests/test_phase_149n_rollback_approval_evidence_canonical_provenance_hardening.py

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

2026-08-04T20:00:03.511323+02:00
