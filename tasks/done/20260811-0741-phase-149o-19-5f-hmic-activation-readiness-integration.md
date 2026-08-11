# Task Contract

## Task ID

20260811-0741-phase-149o-19-5f-hmic-activation-readiness-integration

## Title

Phase 149O.19.5F: HMIC Activation-Readiness Integration

## Status

done

## Mode

implementation

## Goal

Wire fresh HMIC active-certification validation into the hardcoded mandatory_consumption_implementation_independently_verified=False readiness item in hatp_mandatory_cutover.py, preserving the six-item HMRC-REQ-054 conjunction and fresh lock-held activation recheck. No real certification/activation.

## Allowed Files

- src/pcae/core/hatp_mandatory_cutover.py
- tests/test_phase_149o_19_5f_hmic_activation_readiness_integration.py
- docs/PHASE_149O_19_5F_HMIC_ACTIVATION_READINESS_INTEGRATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tests/test_phase_149o_19_5e_4_hmic_v1_1_24_file_alignment_independent_verification.py
- tests/test_phase_149o_19_hmrc_mandatory_consumption_independent_verification.py
- tests/test_phase_149o_19_5c_hmic_protected_certification_state_store.py
- tests/test_phase_149o_19_5d_hmic_active_certification_validation_engine.py
- tests/test_phase_149o_19_5e_1_hmic_v1_1_validator_admin_identity_contract_evolution.py
- tests/test_phase_149o_19_5e_2_hmic_v1_1_contract_independent_verification.py
- tests/test_phase_149o_19_5e_3_hmic_v1_1_24_file_production_identity_alignment.py
- tests/test_phase_149o_19_3_hmic_contract_independent_verification.py
- tests/test_phase_149o_19_3r_hmic_frozen_file_set_contract_repair.py
- tests/test_phase_149o_19_3r_1_hmic_frozen_identity_repair_independent_reverification.py
- tests/test_phase_149o_19_5e_hmic_protected_admin_certification_revocation.py
- tests/test_phase_149o_19_5a_hmic_certification_models_canonical_parsing.py
- tasks/done/20260811-0102-idle-awaiting-next-governed-phase-post-149o-19-5e-4.md
- tasks/DONE.md
- tasks/active/20260811-0741-phase-149o-19-5f-hmic-activation-readiness-integration.md

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

2026-08-11T07:41:23.449176+02:00
