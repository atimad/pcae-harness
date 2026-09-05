# Task Contract

## Task ID

20260905-1535-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-30r-5r-2-1r-1r-2r-1r-1r-1r-1-1r-1r-1r-1r-1r-1r-1r-1r-batch-013-causal-isolation-f-5-hold-re-adjudication

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R: batch-013 causal isolation, F-5 hold re-adjudication

## Status

done

## Mode

diagnostic

## Goal

Continue campaign RHAMP-XTEST-IDENTITY-TRACE/1; bisect batch-013; adjudicate F-5 hold

## Allowed Files

- tasks/**
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/evidence/RHAMP_XTEST_CHECKPOINT_current.json
- .pcae/evidence/RHAMP_XTEST_CORPUS_1_experiment_log.md
- .pcae/evidence/RHAMP_XTEST_INVOCATION_LOG_PHASE_1R.jsonl
- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_1r_1r_1r_1_1r_1r_1r_1r_1r_1r_1r_1r_batch013_causal_isolation_iv.py
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2R_1R_1R_1R_1_1R_1R_1R_1R_1R_1R_1R_1R_BATCH013_CAUSAL_ISOLATION.md

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

2026-09-05T15:35:12.222912+02:00
