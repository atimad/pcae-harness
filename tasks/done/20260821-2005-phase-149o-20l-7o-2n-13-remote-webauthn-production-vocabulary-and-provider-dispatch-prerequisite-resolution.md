# Task Contract

## Task ID

20260821-2005-phase-149o-20l-7o-2n-13-remote-webauthn-production-vocabulary-and-provider-dispatch-prerequisite-resolution

## Title

Phase 149O.20L.7O.2N.13: Remote WebAuthn Production Vocabulary and Provider-Dispatch Prerequisite Resolution

## Status

done

## Mode

implementation

## Goal

Additively widen hatp_hardware_credentials.py's _PROTOCOL_VALUES to include WEBAUTHN and centralize hatp_hardware_credential_admin.py's duplicated closed-vocabulary check onto the canonical definition, repairing NBF-149O.20L.7O.2N.12-2; independently re-derive and dispose of NBF-149O.20L.7O.2N.12-1 (provider-dispatch boundary) without amending the production factory

## Allowed Files

- src/pcae/core/hatp_hardware_credentials.py
- src/pcae/core/hatp_hardware_credential_admin.py
- tests/test_phase_149o_20l_7o_2n_13_hrwp_protocol_vocabulary_and_provider_dispatch_prerequisite.py
- tests/test_phase_149o_20l_7o_2n_11_hrwp_001_protocol_name_vocabulary_repair.py
- tests/test_phase_149o_20l_7o_2n_12_hrwp_001_protocol_name_vocabulary_repair_independent_verification.py
- tests/test_phase_149o_20l_7o_2n_8_hrwp_001_independent_verification.py
- tests/test_phase_149o_20l_7o_2n_1_fido2_enrollment_pre_hardware_governance_confirmation_ordering_narrow_repair.py
- tests/test_phase_149o_20l_7o_2m_1_hmic_v1_7_independent_verification.py
- tests/test_phase_149o_20l_7o_2h_1_hmic_trust_enrollment_signing_authority_scope_alignment_independent_verification.py
- tests/test_phase_149o_20l_7o_2h_hmic_trust_enrollment_signing_closure_limb_d.py
- tests/test_phase_149o_20l_7o_2l_1_hatp_trust_enrollment_admin_entrypoint_implementation.py
- tests/test_phase_149o_20l_7o_2l_3_hatp_hardware_credential_admin_recovery_authority_narrow_repair.py
- PROJECT_STATUS.md
- CHANGELOG.md
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

TBD

## Forbidden Changes

- TBD

## Acceptance Criteria

- TBD

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-21T20:05:33.624341+02:00
