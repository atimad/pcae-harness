# Task Contract

## Task ID

20260807-1942-phase-149o-10-hatp-signing-ceremony-evidence-store-contract-independent-verification

## Title

Phase 149O.10: HATP Signing Ceremony + Evidence Store Contract Independent Verification

## Status

done

## Mode

documentation

## Goal

Independently verify HSCE-001 v1.0 (HATP Signing Ceremony + Evidence Store Contract): attack all 20 items in section 38's mandatory attack matrix, reconfirm AG5 CLI entry-point inventory, reconfirm no production source or HATP-001/RAE-001 contract text modified. Verification-only, no implementation. Also plan (not implement) a repair task for a bootstrap-readiness classifier bug found in src/pcae/commands/session.py.

## Allowed Files

- docs/PHASE_149O_10_HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT_INDEPENDENT_VERIFICATION.md
- tests/test_phase_149o_10_hatp_signing_ceremony_evidence_store_contract_independent_verification.py
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/active/*
- tasks/done/*
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

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

2026-08-07T19:42:55.206033+02:00
