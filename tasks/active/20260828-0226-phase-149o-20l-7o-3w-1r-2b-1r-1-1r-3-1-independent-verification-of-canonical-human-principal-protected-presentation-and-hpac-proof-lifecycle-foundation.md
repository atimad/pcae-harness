# Task Contract

## Task ID

20260828-0226-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-3-1-independent-verification-of-canonical-human-principal-protected-presentation-and-hpac-proof-lifecycle-foundation

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.3.1: Independent Verification of Canonical Human-Principal, Protected-Presentation, and HPAC Proof-Lifecycle Foundation

## Status

active

## Mode

verification

## Goal

Independently verify Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.3 from primary contracts, pre-phase state, current source, Git/lifecycle artifacts, and fresh adversarial tests; document findings only, with no production repair, revert, Layer 3, or runtime activation

## Allowed Files

- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_3_1_INDEPENDENT_VERIFICATION_CANONICAL_HUMAN_PRINCIPAL_PROTECTED_PRESENTATION_HPAC_PROOF_LIFECYCLE_FOUNDATION.md
- tests/test_hpac_foundation_independent_verification_3w1r2b1r111r31.py
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- .pcae/fast-green-attribution/**
- .pcae/phase-reports/**3-1*
- .pcae/finalization-transactions/**3-1*
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- tasks/active/**
- tasks/done/**

## Forbidden Files

- src/pcae/**
- docs/contracts/**
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_3_CANONICAL_HUMAN_PRINCIPAL_PROTECTED_PRESENTATION_HPAC_PROOF_LIFECYCLE_FOUNDATION_IMPLEMENTATION.md
- .pcae/phase-reports/20260828-001541-149O.20L.7O.3W.1R.2B.1R.1.1R.3.json
- .pcae/phase-reports/20260828-001541-149O.20L.7O.3W.1R.2B.1R.1.1R.3.md
- .pcae/finalization-transactions/149O.20L.7O.3W.1R.2B.1R.1.1R.3.json


## Allowed Zones

- docs
- tests
- tasks
- config

## Forbidden Zones

- core
- commands
- cltr
- cli
- schema_runtime
- governance
- interactive_workflow
- authority_evaluation
- aesic
- scripts
- hooks
- package
- policy
- session

## Allowed Dependencies

- tests -> *
- docs -> *
- tasks -> *
- config -> config

## Forbidden Dependencies

- core -> tests
- core -> docs

## Enforcement Mode

strict

## Forbidden Changes

- No production-source or contract amendment
- No HPAC implementation repair
- No revert, history rewrite, force push, or amendment of the historical .3 report
- No Layer 3, B1/B7/N1/N2 production integration, FIDO2, protected UI, PB integration, or runtime execution
- No Runtime Enforcement, Shell Gate, provider, network, release, or Dell work
- No delegated agent may commit, finalize, push, or exercise consequential completion authority
- Documentation/test commits, governed primary-agent phase finalization, and ordinary push of .3.1 evidence are permitted by the human-authorized phase

## Acceptance Criteria

- Independently reconstruct the complete .3 commit/lifecycle sequence and adjudicate delegated authority
- Verify each HPAC foundation trust boundary against primary contracts with a fresh adversarial suite
- Demonstrate fixed-SHA pre/current regression equivalence by node ID and preserve the runtime boundary

## Acceptance Checks

- python -m pytest tests/test_hpac_foundation_independent_verification_3w1r2b1r111r31.py -q
- python -m pytest tests/test_hpac_foundation_independent_verification_3w1r2b1r111r31.py tests/test_hpac_approval_presentation.py tests/test_hpac_authentication_proof.py tests/test_hpac_authenticator_deterministic.py tests/test_hpac_authority_consumption.py tests/test_hpac_lifecycle.py tests/test_hpac_principal_registry.py -q
- pcae status coherence
- pcae health
- pcae check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-28T02:26:12.816964+02:00
