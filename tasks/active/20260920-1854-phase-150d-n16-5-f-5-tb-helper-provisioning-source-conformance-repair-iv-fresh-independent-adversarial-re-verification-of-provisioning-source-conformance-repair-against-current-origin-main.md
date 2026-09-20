# Task Contract

## Task ID

20260920-1854-phase-150d-n16-5-f-5-tb-helper-provisioning-source-conformance-repair-iv-fresh-independent-adversarial-re-verification-of-provisioning-source-conformance-repair-against-current-origin-main

## Title

Phase 150D (N16-5-F-5-TB-HELPER-PROVISIONING-SOURCE-CONFORMANCE-REPAIR-IV): fresh independent adversarial re-verification of provisioning source-conformance repair against current origin/main

## Status

active

## Mode

implementation

## Goal

Fresh, independent adversarial re-verification of the provisioning source-conformance repair (removal of configure_privileged_helper / configure_presentation_mechanism from helper privileged mutation path) against current origin/main after 150B/150C, without reusing the held IV's evidence or committing production/contract changes.

## Allowed Files

- docs/PHASE_N16_5_F_5_TB_HELPER_PROVISIONING_SOURCE_CONFORMANCE_REPAIR_IV.md
- docs/evidence/provisioning-source-conformance-iv/*
- tests/test_n16_5_f_5_tb_helper_provisioning_source_conformance_repair_iv.py
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/*
- tasks/done/*
- .pcae/*
- .pcae/fast-green-attribution/*

## Forbidden Files

- src/pcae/**
- docs/contracts/**

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

- Both forbidden provisioning operations independently confirmed absent/fail-closed on every helper dispatch path against current source
- Fresh Fast Green attribution shows attributable_failures: []
- Zero src/pcae/** and zero docs/contracts/** changes

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-20T18:54:01.295995+02:00
