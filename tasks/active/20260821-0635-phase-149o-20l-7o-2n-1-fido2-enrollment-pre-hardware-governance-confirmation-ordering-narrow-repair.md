# Task Contract

## Task ID

20260821-0635-phase-149o-20l-7o-2n-1-fido2-enrollment-pre-hardware-governance-confirmation-ordering-narrow-repair

## Title

Phase 149O.20L.7O.2N.1: FIDO2 Enrollment Pre-Hardware Governance Confirmation Ordering Narrow Repair

## Status

active

## Mode

implementation

## Goal

Repair Blocking finding B-149O.20L.7O.2N-1: reorder scripts/hatp_hardware_credential_admin.py's enroll ceremony so the governance confirmation gate is established before any real FIDO2 makeCredential/hardware provider call, guaranteeing declined confirmation => zero provider/hardware/writer calls. Synthetic-provider only. No real hardware, no fido2 install, no HMIC/contract/Principal/Signer changes.

## Allowed Files

- scripts/hatp_hardware_credential_admin.py
- tests/test_hatp_hardware_credential_admin_script.py
- tests/test_phase_149o_20l_7o_2n_1_fido2_enrollment_pre_hardware_governance_confirmation_ordering_narrow_repair.py
- tests/test_phase_149o_20l_7o_2m_1_hmic_v1_7_independent_verification.py
- tests/test_phase_149o_20l_7o_2n_post_hmic_trust_enrollment_dag_and_fido2_authorization.py
- docs/PHASE_149O_20L_7O_2N_1_FIDO2_ENROLLMENT_PRE_HARDWARE_GOVERNANCE_CONFIRMATION_ORDERING_NARROW_REPAIR.md
- PROJECT_STATUS.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/done/20260821-0245-idle-awaiting-next-governed-phase-post-149o-20l-7o-2n.md
- tasks/active/20260821-0635-phase-149o-20l-7o-2n-1-fido2-enrollment-pre-hardware-governance-confirmation-ordering-narrow-repair.md

## Forbidden Files

- TBD


## Allowed Zones

- docs
- tests
- tasks
- config
- scripts

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

- Reproduce pre-repair defect: provider enrollment call occurs before confirmation is checked
- Post-repair: declined confirmation guarantees provider enrollment=0, makeCredential=0, register_credential=0, no HardwareCredentialRecord
- Post-repair: successful synthetic enrollment sequence is confirmation-accepted -> provider enrollment exactly once -> register_credential
- One-hardware-ceremony invariant preserved; persistence retry reuses identical evidence, no second ceremony
- No caller-supplied credential identity introduced; revoke, Principal/Signer script, core writer, and contracts remain byte-identical
- No real hardware touched, no fido2 install on Dell, no Dell connection

## Acceptance Checks

- python -m pytest -n auto

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-21T06:35:19.913452+02:00
