# Task Contract

## Task ID

20260828-0149-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-3-canonical-human-principal-protected-presentation-and-hpac-proof-lifecycle-foundation-implementation

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.3: Canonical Human-Principal, Protected-Presentation, and HPAC Proof-Lifecycle Foundation Implementation

## Status

done

## Mode

implementation

## Goal

Implement Layer 1-2 foundation: HumanPrincipalRegistry, TrustedApprovalPresentationEvidence, HumanAuthenticationProof, HPAC hash-chained lifecycle models/stores, deterministic non-real authenticator/presentation-mechanism fixtures, and inert Gate-9 consumption model/store, realizing HPAC-001 v2.0. No PB/runtime_authority.py change, no real FIDO2/UI, no hardware, no Gate-5/9 wiring.

## Allowed Files

- src/pcae/core/hpac_foundation.py
- src/pcae/core/human_principal_registry.py
- src/pcae/core/human_authenticator.py
- src/pcae/core/human_authenticator_deterministic.py
- src/pcae/core/approval_presentation.py
- src/pcae/core/approval_presentation_deterministic.py
- src/pcae/core/human_authentication_proof.py
- src/pcae/core/hpac_lifecycle.py
- src/pcae/core/runtime_invocation_authority_consumption.py
- tests/test_hpac_principal_registry.py
- tests/test_hpac_authenticator_deterministic.py
- tests/test_hpac_approval_presentation.py
- tests/test_hpac_authentication_proof.py
- tests/test_hpac_lifecycle.py
- tests/test_hpac_authority_consumption.py
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_3_CANONICAL_HUMAN_PRINCIPAL_PROTECTED_PRESENTATION_HPAC_PROOF_LIFECYCLE_FOUNDATION_IMPLEMENTATION.md
- PROJECT_STATUS.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/done/20260828-0117-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-2-human-principal-authentication-protected-approval-presentation-and-proof-lifecycle-implementation-planning.md

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

- TBD

## Acceptance Criteria

- All eight foundation modules implemented per HPAC-001 v2.0; adversarial/trust-forgery tests pass; zero regressions in runtime_authority/hatp/PB/dry-runtime test slices; runtime remains Observed/observe/unavailable; no PB/runtime_authority.py/hardware/Gate-5/9 change

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-28T01:49:19.277282+02:00
