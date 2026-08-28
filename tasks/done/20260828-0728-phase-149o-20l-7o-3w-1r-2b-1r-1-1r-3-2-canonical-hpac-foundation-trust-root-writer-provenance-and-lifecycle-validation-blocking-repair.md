# Task Contract

## Task ID

20260828-0728-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-3-2-canonical-hpac-foundation-trust-root-writer-provenance-and-lifecycle-validation-blocking-repair

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.3.2: Canonical HPAC Foundation Trust-Root, Writer-Provenance, and Lifecycle-Validation Blocking Repair

## Status

done

## Mode

implementation

## Goal

Repair only the four trust-foundation defects independently reproduced by
Phase .3.1: canonical principal-registry authority and fixture provenance,
protected-presentation installation/writer/attestation provenance, canonical
proof-writer provenance and stage separation, and authoritative HPAC genesis,
predecessor-chain validation, and fork rejection. Preserve Gate 9 as inert;
do not begin Layer 3, PB/runtime integration, real authentication, or contract
evolution.

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- src/pcae/core/human_principal_registry.py
- src/pcae/core/human_authenticator.py
- src/pcae/core/human_authenticator_deterministic.py
- src/pcae/core/approval_presentation.py
- src/pcae/core/approval_presentation_deterministic.py
- src/pcae/core/human_authentication_proof.py
- src/pcae/core/hpac_lifecycle.py
- src/pcae/core/runtime_invocation_authority_consumption.py
- src/pcae/core/hpac_foundation.py
- tests/test_hpac_foundation_trust_root_repair_3w1r2b1r111r32.py
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_3_2_CANONICAL_HPAC_FOUNDATION_TRUST_ROOT_WRITER_PROVENANCE_LIFECYCLE_VALIDATION_BLOCKING_REPAIR.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- .pcae/fast-green-attribution/**
- .pcae/phase-reports/**3-2*
- .pcae/finalization-transactions/**3-2*

## Forbidden Files

- docs/contracts/**
- src/pcae/core/runtime_authority.py
- src/pcae/core/runtime_dispatch_permission.py
- src/pcae/core/permission_broker.py
- src/pcae/core/permission_broker_foundation.py
- src/pcae/core/runtime_enforcement.py
- src/pcae/core/shell_gate.py
- pyproject.toml
- docs/releases/**


## Allowed Zones

- core
- tests
- docs
- tasks
- config

## Forbidden Zones

- commands
- cli
- scripts
- hooks
- package
- policy
- session
- authority_evaluation

## Allowed Dependencies

- core -> core
- tests -> core
- tests -> tests
- docs -> *
- tasks -> *
- config -> config

## Forbidden Dependencies

- core -> tests
- core -> docs

## Enforcement Mode

strict

## Forbidden Changes

- No normative contract change
- No historical `.3` or `.3.1` evidence rewrite, revert, rebase, or amendment
- No Layer 3 verifier, verified-principal resolver, approval projection, or B1/B7/N1/N2 production repair
- No PB, Runtime Enforcement, Shell Gate, RDGO Gate-5/9/10 production wiring, subprocess, provider, network, credential, hardware, or external effect
- No real FIDO2, WebAuthn, CTAP, PAM, biometric, keychain, enrollment, protected UI, approval CLI, or enrollment CLI
- No release, version, tag, publication, Dell, private-research, or article work
- No delegated agent commit, finalization, push, or consequential completion authority
- Primary-operator documentation/test/source commits, canonical phase finalization, and ordinary governed push are authorized

## Acceptance Criteria

- All four `.3.1` trust defects are repaired with caller construction, copied bytes, public digests, and caller paths remaining non-authoritative
- Fixture principal, deterministic presentation, deterministic authenticator, and deterministic proof remain durably non-real and real-authority-ineligible
- Authoritative genesis, complete predecessor validation, disconnected-chain rejection, and immediate/deep fork rejection are implemented
- Gate-9 primitive remains inert; PB/runtime integration and B1/B7/N1/N2 repair remain absent
- Runtime remains Observed / observe / unavailable and unexplained attributable functional regressions equal zero
- Each successful repair is reported as REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED

## Acceptance Checks

- pcae status coherence
- pcae health
- pcae check
- python -m pytest tests/test_hpac_foundation_trust_root_repair_3w1r2b1r111r32.py -q
- python -m pytest tests/test_hpac_foundation_trust_root_repair_3w1r2b1r111r32.py tests/test_hpac_approval_presentation.py tests/test_hpac_authentication_proof.py tests/test_hpac_authenticator_deterministic.py tests/test_hpac_authority_consumption.py tests/test_hpac_lifecycle.py tests/test_hpac_principal_registry.py -q

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-28T07:28:37.590357+02:00
