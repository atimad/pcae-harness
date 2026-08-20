# Task Contract

## Task ID

20260820-1229-hatp-trust-enrollment-standalone-protected-admin-entry-point-implementation-149o-20l-7o-2l-1

## Title

HATP Trust-Enrollment Standalone Protected Admin Entry-Point Implementation (149O.20L.7O.2L.1)

## Status

done

## Mode

implementation

## Goal

Implement scripts/hatp_hardware_credential_admin.py and scripts/hatp_principal_signer_admin.py as thin, fail-closed Protected Admin CLI entrypoints over the existing HATP core Trust-Enrollment writers; no hardware touch, no HardwareCredentialRecord/Principal/Signer/DeploymentBinding creation, no HMIC change.

## Allowed Files

- scripts/hatp_hardware_credential_admin.py
- scripts/hatp_principal_signer_admin.py
- tests/test_hatp_hardware_credential_admin_script.py
- tests/test_hatp_principal_signer_admin_script.py
- tests/test_phase_149o_20l_7o_2l_post_hmic_activation_trust_enrollment_dag.py
- tests/test_phase_149o_20l_7o_2l_1_hatp_trust_enrollment_admin_entrypoint_implementation.py
- tests/test_phase_149o_20l_7o_2h_3_hmic_paths_source_scope_and_seven_contract_consistency_independent_verification.py
- tests/test_phase_149o_20l_7o_2k_hatp_prerequisite_dag_correction_and_next_real_effect_node_selection.py
- tests/test_phase_149o_20l_7o_2k_4_post_certificationrecord_dag_re_derivation.py
- docs/PHASE_149O_20L_7O_2L_1_HATP_TRUST_ENROLLMENT_ADMIN_ENTRYPOINT_IMPLEMENTATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/active/20260820-1229-hatp-trust-enrollment-standalone-protected-admin-entry-point-implementation-149o-20l-7o-2l-1.md

## Forbidden Files

- TBD


## Allowed Zones

- tasks
- docs
- tests
- scripts
- config

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

- Both admin scripts implemented as thin wrappers over existing core writers
- No real hardware/Principal/Signer/DeploymentBinding/HMIC mutation
- Focused tests pass; fast_green clean

## Acceptance Checks

- python -m pytest tests/test_hatp_hardware_credential_admin_script.py tests/test_hatp_principal_signer_admin_script.py -q

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-20T12:29:35.893650+02:00
