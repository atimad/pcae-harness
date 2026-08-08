# Task Contract

## Task ID

20260808-1200-phase-149o-13-hatp-signing-ceremony-evidence-store-independent-implementation-verification

## Title

Phase 149O.13: HATP Signing Ceremony + Evidence Store Independent Implementation Verification

## Status

done

## Mode

validation

## Goal

Independently reconstruct and adversarially verify HSCE-001 v1.1 implementation (149O.12A/B/C): model/store, signing ceremony/TOCTOU, CLI, all 21 mandatory + 4 extra attacks, production dependency closure, no authority conflation, no rollback-consumption side effects. Verification-only: no production/contract changes.

## Allowed Files

- tests/test_phase_149o_13_hatp_signing_ceremony_evidence_store_independent_verification.py
- docs/PHASE_149O_13_HATP_SIGNING_CEREMONY_EVIDENCE_STORE_INDEPENDENT_IMPLEMENTATION_VERIFICATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/DONE.md
- tasks/active/*
- tasks/done/*

## Forbidden Files

- src/pcae/core/hatp_signed_evidence.py
- src/pcae/core/hatp_evidence_store.py
- src/pcae/core/hatp_signing_ceremony.py
- src/pcae/commands/hatp.py
- src/pcae/cli.py
- docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md
- docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md
- docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md

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

- All 21 mandatory + 4 extra attacks independently reproduced with documented results
- No production source or contract files modified

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes (Fast Green, no new failures)

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-08T12:00:36.111900+02:00
