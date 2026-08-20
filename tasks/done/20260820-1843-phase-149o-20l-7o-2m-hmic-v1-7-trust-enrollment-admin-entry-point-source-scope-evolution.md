# Task Contract

## Task ID

20260820-1843-phase-149o-20l-7o-2m-hmic-v1-7-trust-enrollment-admin-entry-point-source-scope-evolution

## Title

Phase 149O.20L.7O.2M: HMIC v1.7 Trust-Enrollment Admin Entry-Point Source-Scope Evolution

## Status

done

## Mode

contract_evolution

## Goal

Widen HMIC-001 v1.6 -> v1.7's frozen authority-bearing source/content identity 36 -> 38 by binding the two newly-verified standalone Trust-Enrollment admin entry points; align production; no real Trust-Enrollment/certification/HATP effect

## Allowed Files

- src/pcae/core/hatp_mandatory_certification.py
- docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md
- tests/test_phase_149o_20l_7o_2m_hmic_v1_7_trust_enrollment_admin_entrypoint_source_scope_evolution.py
- tests/test_phase_149o_20l_7o_2h_3_hmic_paths_source_scope_and_seven_contract_consistency_independent_verification.py
- tests/test_phase_149o_20l_7o_2k_2_hac_dell_governed_source_synchronization_redeployment_and_source_parity_restoration.py
- tests/test_phase_149o_20l_7o_2l_1_hatp_trust_enrollment_admin_entrypoint_implementation.py
- tests/test_phase_149o_20l_7o_2l_3_hatp_hardware_credential_admin_recovery_authority_narrow_repair.py
- tests/test_phase_149o_20l_7o_2l_4_hatp_hardware_credential_admin_recovery_authority_repair_independent_verification.py
- tests/test_phase_149o_20l_7o_2l_post_hmic_activation_trust_enrollment_dag.py
- docs/PHASE_149O_20L_7O_2M_HMIC_V1_7_TRUST_ENROLLMENT_ADMIN_ENTRY_POINT_SOURCE_SCOPE_EVOLUTION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/active/20260820-1806-idle-awaiting-next-governed-phase-post-149o-20l-7o-2l-4.md
- tasks/done/20260820-1806-idle-awaiting-next-governed-phase-post-149o-20l-7o-2l-4.md
- tests/test_phase_149o_20l_7o_2h_2_hmic_paths_source_scope_and_ceremony_consistency_repair.py
- tests/test_phase_149o_20l_7o_2h_hmic_trust_enrollment_signing_closure_limb_d.py
- tests/test_phase_149o_20l_7o_2i_hatp_remaining_prerequisite_state_and_sequencing_reconciliation.py
- tests/test_phase_149o_20l_7o_2j_hatp_class_b_real_host_protected_root_provisioning_authorization.py
- tests/test_phase_149o_20l_7o_2k_hatp_prerequisite_dag_correction_and_next_real_effect_node_selection.py
- tests/test_phase_149o_20l_7o_2g_1_hmic_target_set_reconciliation.py

## Forbidden Files

- src/pcae/core/hatp_hardware_credential_admin.py
- src/pcae/core/hatp_principal_signer_admin.py
- scripts/hatp_hardware_credential_admin.py
- scripts/hatp_principal_signer_admin.py
- .pcae/certifications/**
- .pcae/hatp/**
- hac-dell/**


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

- HMIC-001 v1.7 frozen source/content identity widened to exactly 38 members (36 + the two standalone Trust-Enrollment admin scripts); contract identity remains exactly 7; production aligned; no real Trust-Enrollment, certification, or HATP effect

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-20T18:43:22.010313+02:00
