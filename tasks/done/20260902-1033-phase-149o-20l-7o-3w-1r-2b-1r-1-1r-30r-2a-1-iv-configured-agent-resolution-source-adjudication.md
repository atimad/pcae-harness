# Task Contract

## Task ID

20260902-1033-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-30r-2a-1-iv-configured-agent-resolution-source-adjudication

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.1: IV configured-agent resolution source adjudication

## Status

done

## Mode

documentation

## Goal

Independent verification of the .1R.30R.2A configured-agent-principal resolution source adjudication: re-derive the F-1 gap and three distinct predicates from HPAC-PAWA-001 v1.0 + src/pcae; stress-test R1 (symbolic account + live uid/gids) against group drift, UID reuse, deletion/recreation, rename, rollback, migration, same-UID topology; adjudicate pure-symbolic vs hybrid account-instance binding; independently re-derive R2/R3/R4 rejections, the v1.1 MINOR verdict, atomicity, and the D1 decomposition against CPIPC-001. Verification only; no src/pcae, no contracts, no v1.1 authoring, no implementation.

## Allowed Files

- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_2A_1_INDEPENDENT_VERIFICATION_OF_THE_CONFIGURED_AGENT_PRINCIPAL_RESOLUTION_SOURCE_CONTRACT_COMPATIBILITY_ADJUDICATION.md
- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_2a_1_configured_agent_resolution_source_iv.py
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DECISIONS.md
- tasks/DONE.md
- tasks/TODO.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/active/20260902-1033-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-30r-2a-1-iv-configured-agent-resolution-source-adjudication.md
- tasks/done/20260902-1015-idle-awaiting-next-governed-phase-post-149o-20l-7o-3w-1r-2b-1r-1-1r-30r-2a-dedicated-iv-1r-30r-2a-1-recommended-next.md

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

2026-09-02T10:33:13.896281+02:00
