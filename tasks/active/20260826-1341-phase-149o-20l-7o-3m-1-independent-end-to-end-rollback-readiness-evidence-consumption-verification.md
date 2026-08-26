# Task Contract

## Task ID

20260826-1341-phase-149o-20l-7o-3m-1-independent-end-to-end-rollback-readiness-evidence-consumption-verification

## Title

Phase 149O.20L.7O.3M.1: Independent End-to-End Rollback Readiness / Evidence Consumption Verification

## Status

active

## Mode

verification

## Goal

Independently verify pre- and post-3M rollback evidence preparation, consumption, authority isolation, freshness, persistence, CLI visibility, and regression safety without trusting 3M evidence or modifying production source.

## Allowed Files

- docs/PHASE_149O_20L_7O_3M_1_INDEPENDENT_END_TO_END_ROLLBACK_READINESS_EVIDENCE_CONSUMPTION_VERIFICATION.md
- tests/test_phase_149o_20l_7o_3m_1_independent_rollback_readiness_evidence_consumption_verification.py
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- tasks/active/**
- tasks/done/**
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- .pcae/fast-green-attribution/*

## Forbidden Files

- src/pcae/**

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

- Independently establish whether real pre-3M rollback computed and consumed file_plan and divergence_check without prior dry-run
- Verify evidence visibility is non-authoritative and preserves Permission Broker, HATP, human-trigger, effect, and runtime semantics
- Adjudicate readiness-contract need and promotion-time persistence from current and pre-3M evidence
- Zero Blocking findings or stop and recommend the smallest repair phase

## Acceptance Checks

- pcae health passes
- pcae check passes
- pcae status coherence passes
- fresh 3M.1 tests pass
- targeted and shared regressions have zero attributable failures
- Fast Green attribution reports zero attributable regressions
- runtime remains Observed/observe/unavailable
- origin/main..HEAD is zero after governed push

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-26T13:41:03.997780+02:00
