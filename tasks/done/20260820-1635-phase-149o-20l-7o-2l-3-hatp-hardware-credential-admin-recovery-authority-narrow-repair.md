# Task Contract

## Task ID

20260820-1635-phase-149o-20l-7o-2l-3-hatp-hardware-credential-admin-recovery-authority-narrow-repair

## Title

Phase 149O.20L.7O.2L.3: HATP Hardware-Credential Admin Recovery Authority Narrow Repair

## Status

done

## Mode

implementation

## Goal

Remove unauthorized public recover subcommand from scripts/hatp_hardware_credential_admin.py per 2L.2 Blocking finding; preserve safe in-process enrollment retry; no contract/core-writer changes

## Allowed Files

- scripts/hatp_hardware_credential_admin.py
- tests/test_phase_149o_20l_7o_2l_3_hatp_hardware_credential_admin_recovery_authority_narrow_repair.py
- tests/test_phase_149o_20l_7o_2l_2_hatp_trust_enrollment_admin_entrypoint_independent_verification.py
- tests/test_phase_149o_20l_7o_2l_1_hatp_trust_enrollment_admin_entrypoint_implementation.py
- tests/test_hatp_hardware_credential_admin_script.py
- docs/PHASE_149O_20L_7O_2L_3_HATP_HARDWARE_CREDENTIAL_ADMIN_RECOVERY_AUTHORITY_NARROW_REPAIR.md
- CHANGELOG.md
- PROJECT_STATUS.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/DONE.md
- tasks/active/20260820-1635-phase-149o-20l-7o-2l-3-hatp-hardware-credential-admin-recovery-authority-narrow-repair.md
- tasks/done/20260820-1635-phase-149o-20l-7o-2l-3-hatp-hardware-credential-admin-recovery-authority-narrow-repair.md
- tasks/active/20260820-1526-idle-awaiting-next-governed-phase-post-149o-20l-7o-2l-2.md
- tasks/done/20260820-1526-idle-awaiting-next-governed-phase-post-149o-20l-7o-2l-2.md

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

- public recover subcommand removed from scripts/hatp_hardware_credential_admin.py
- no caller-supplied credential identity path can create a HardwareCredentialRecord
- enroll/revoke semantics unchanged and re-verified
- fast_green regression comparison shows zero attributable regressions

## Acceptance Checks

- python -m pytest tests/test_phase_149o_20l_7o_2l_3_hatp_hardware_credential_admin_recovery_authority_narrow_repair.py -v

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-20T16:35:13.373094+02:00
