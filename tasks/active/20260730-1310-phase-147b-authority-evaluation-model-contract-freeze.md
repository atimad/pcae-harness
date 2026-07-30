# Task Contract

## Task ID

20260730-1310-phase-147b-authority-evaluation-model-contract-freeze

## Title

Phase 147B: Authority Evaluation Model Contract Freeze

## Status

active

## Mode

read_only

## Goal

Freeze the Authority Evaluation Model contract (eligible authority, evaluation semantics, evidence, failure model, interactions with CHGR-001/IWPC-001/IWC-001/PEC-001/TAMC-001/GAC-001) per Phase 147A's C-1 recommendation; contract-freeze only, no implementation, no runtime change.

## Allowed Files

- docs/contracts/AUTHORITY_EVALUATION_MODEL_CONTRACT.md
- docs/PHASE_147B_AUTHORITY_EVALUATION_MODEL_CONTRACT_FREEZE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/done/20260730-1239-idle-awaiting-next-governed-phase-post-147a.md
- tasks/active/20260730-1310-phase-147b-authority-evaluation-model-contract-freeze.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- .pcae/phase-reports/**

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

2026-07-30T13:10:31.762088+02:00
