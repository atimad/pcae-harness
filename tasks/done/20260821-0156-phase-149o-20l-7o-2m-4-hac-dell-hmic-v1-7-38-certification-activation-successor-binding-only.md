# Task Contract

## Task ID

20260821-0156-phase-149o-20l-7o-2m-4-hac-dell-hmic-v1-7-38-certification-activation-successor-binding-only

## Title

Phase 149O.20L.7O.2M.4: hac-dell HMIC v1.7/38 Certification Activation -- Successor Binding Only

## Status

done

## Mode

real-effect

## Goal

Repoint the active HMIC CertificationBinding on hac-dell from the old v1.6/36 certification to the new v1.7/38 certification, transitioning the validator IMPLEMENTATION_MISMATCH -> VALID and HMIC readiness FALSE -> TRUE, without creating/revoking any record, touching FIDO2/PIV, or activating HATP.

## Allowed Files

- docs/PHASE_149O_20L_7O_2M_4_HAC_DELL_HMIC_V1_7_38_CERTIFICATION_ACTIVATION_SUCCESSOR_BINDING_ONLY.md
- tests/test_phase_149o_20l_7o_2m_4_hac_dell_hmic_v1_7_38_certification_activation_successor_binding_only.py
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- PROJECT_STATUS.md
- tasks/active/*.md
- tasks/done/*.md

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

- Active binding on hac-dell repointed from old to new certification via the production activate ceremony only
- Both CertificationRecords remain byte-for-field unchanged
- Validator transitions IMPLEMENTATION_MISMATCH -> VALID and readiness FALSE -> TRUE, independently re-derived
- No Trust-Enrollment/FIDO2/HATP-activation state created

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-21T01:56:11.516582+02:00
