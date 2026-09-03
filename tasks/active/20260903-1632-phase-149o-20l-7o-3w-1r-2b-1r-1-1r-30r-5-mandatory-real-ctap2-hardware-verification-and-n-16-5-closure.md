# Task Contract

## Task ID

20260903-1632-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-30r-5-mandatory-real-ctap2-hardware-verification-and-n-16-5-closure

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5: Mandatory Real-CTAP2-Hardware Verification and N-16-5 Closure

## Status

active

## Mode

validation

## Goal

Certification/verification phase: perform the mandatory RHAMP-REQ-152 real-CTAP2 hardware ceremony, reconcile the .30R.4R.2 F-1 guard + sibling stale .1R.19R/.30R.1 guards, and adjudicate N-16-5 closure. RESULT: BLOCKED -- the production NativeCtap2Provider (hpac_rhamp_ctap2.py) passes options={'uv': True} to authenticatorMakeCredential and authenticatorGetAssertion, which every attached FIDO_2_1 authenticator rejects with CTAP 0x2C INVALID_OPTION; neither real ceremony can complete. Repairing the CTAP2.1 PIN/UV auth-protocol handshake is a production change outside this certification phase's scope (prompt section 55). N-16-5 remains NOT CLOSED.

## Allowed Files

- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5_N_16_5_MANDATORY_REAL_CTAP2_HARDWARE_VERIFICATION_AND_N_16_5_CLOSURE.md
- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5_hardware_cert_closure.py
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DECISIONS.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/**

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

- TBD

## Acceptance Criteria

- TBD

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-03T16:32:37.311613+02:00
