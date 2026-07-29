# Task Contract

## Task ID

20260730-0110-phase-146l-chgr-cross-artifact-digest-binding-and-duplicate-match-verification-repair

## Title

Phase 146L: CHGR Cross-Artifact Digest-Binding and Duplicate-Match Verification Repair

## Status

active

## Mode

read_write

## Goal

Implement CHGR-REQ-212/CHGR-REQ-213 verifier-only repair in src/pcae/governance/verification.py: fix first-match related-artifact resolution, enforce exact confirmation/provenance record_family+record_id+record_digest reference matching, enforce directed one-way integrity binding (CHGR-REQ-211), and fail closed on duplicate/ambiguous related-artifact matches, while preserving all existing verification protections and legacy Chapter 146 bundle compatibility (CHGR-REQ-215).

## Allowed Files

- src/pcae/governance/verification.py
- tests/test_phase_146l_chgr_cross_artifact_digest_binding_and_duplicate_match_verification_repair.py
- tests/fixtures/chgr/**
- docs/PHASE_146L_*.md
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- .pcae/phase-reports/**
- tests/test_chgr_verification.py
- tests/test_phase_146h3_confirmation_binding_verification_repair.py
- tests/test_phase_146h1_governance_verification_schema_version_repair.py
- tests/test_phase_146g_chgr_schema_envelope_implementation.py

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

- TBD

## Acceptance Criteria

- TBD

## Acceptance Checks

- python -m pytest tests/test_phase_146l_chgr_cross_artifact_digest_binding_and_duplicate_match_verification_repair.py -q
- python -m pytest -m fast_green -n auto -q
- pcae check
- pcae health

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-30T01:10:26.410715+02:00
