# Task Contract

## Task ID

20260918-1855-n16-5-f-5-tb-helper-installation-provisioning-contract-repair-iv-fresh-independent-adversarial-verification

## Title

N16-5-F-5-TB-HELPER-INSTALLATION-PROVISIONING-CONTRACT-REPAIR-IV: fresh independent adversarial verification

## Status

active

## Mode

implementation

## Goal

Fresh independent adversarial IV of N16-5-F-5-TB-HELPER-INSTALLATION-PROVISIONING-CONTRACT-REPAIR: verify F1-A/F1-B repair, Model P-D provenance, contract/source conformance; produce canonical evidence + report; no production behavior change; IV-only

## Allowed Files

- docs/PHASE_N16_5_F_5_TB_HELPER_INSTALLATION_PROVISIONING_CONTRACT_REPAIR_IV.md
- tests/test_n16_5_f5_tb_prov_repair_iv.py
- PROJECT_STATUS.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- CHANGELOG.md
- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json
- tasks/active/*
- tasks/done/*

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

2026-09-18T18:55:59.462507+02:00
