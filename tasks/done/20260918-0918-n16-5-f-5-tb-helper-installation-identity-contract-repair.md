# Task Contract

## Task ID

20260918-0918-n16-5-f-5-tb-helper-installation-identity-contract-repair

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1: Protected Helper Installation Identity, PAWA Identity, PPA Launch Identity, and Configured-Agent Exclusion Contract Reconciliation (N16-5-F-5-TB-HELPER-INSTALLATION-IDENTITY-CONTRACT-REPAIR)

## Status

done

## Mode

implementation

## Goal

N16-5-F-5-TB-HELPER-INSTALLATION-IDENTITY-CONTRACT-REPAIR

## Allowed Files

- docs/**
- tests/**
- .pcae/**
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md

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
- No rollback

## Acceptance Criteria

- Freeze one coherent identity contract model without production mutation.
- Preserve configured-agent exclusion, Model E and the single protected root.
- Attribute all regressions against the canonical predecessor.
- Complete governed reporting/commit/push with successor not begun.

## Acceptance Checks

- pcae status coherence
- pcae health
- pcae check
- python -m pytest -q tests/test_n16_5_f_5_tb_helper_installation_identity_contract_repair.py
- python -c "import json; x=json.load(open('.pcae/phase-completion-metadata.json'))['validation_results']['fast_green']; assert isinstance(x,dict) and not x['attributable_failures']"

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-18T09:18:37.163786+02:00
