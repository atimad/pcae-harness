# Task Contract

## Task ID

20260924-1951-phase-150h-post-finalization-notification-marker-lifecycle-stability-correction

## Title

Phase 150H post-finalization notification-marker lifecycle-stability correction

## Status

done

## Mode

verification

## Goal

Make Phase 150H's own verification suite remain valid after the normal global
notification marker advances from 150G to 150H, without changing any 150G
artifact or production behavior.

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- docs/PHASE_150H_PCAE_LIFECYCLE_PHASE_150G_REPORT_IDENTITY_RECONCILIATION.md
- tests/test_phase_150h_pcae_lifecycle_phase_150g_report_identity_reconciliation.py
- .pcae/**

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
- No source behavior changes outside task/session/handoff governance
- No execution authorization
- No delegated finalization, commit, or push
- No force push, hook bypass, or history rewrite
- No rollback

## Acceptance Criteria

- Fresh Phase 150H suite passes after terminal notification.
- Global latest marker is not misrepresented as immutable per-phase evidence.
- Zero src/pcae/** and docs/contracts/** changes.

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-24T19:51:47.517412+02:00
