# Task Contract

## Task ID

20260820-1132-phase-149o-20l-7o-2k-5-hatp-hmic-certification-activation-existing-certification-binding-only

## Title

Phase 149O.20L.7O.2K.5: HATP HMIC Certification Activation - Existing Certification Binding Only

## Status

active

## Mode

implementation

## Goal

Bind existing HMIC CertificationRecord 2e5f861249d8e70bff53ba2f371d84e37e14eff0bbfcd939902fa7b47d236bd7 as active certification on hac-dell via scripts/hatp_certification_admin.py activate; no new records, no FIDO2/Principal/Signer/DeploymentBinding, no HATP activation.

## Allowed Files

- docs/PHASE_149O_20L_7O_2K_5_HATP_HMIC_CERTIFICATION_ACTIVATION.md
- CHANGELOG.md
- PROJECT_STATUS.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/DONE.md
- tasks/active/20260820-1132-phase-149o-20l-7o-2k-5-hatp-hmic-certification-activation-existing-certification-binding-only.md
- tasks/done/20260820-1104-idle-awaiting-next-governed-phase-post-149o-20l-7o-2k-4.md
- tasks/active/20260820-1104-idle-awaiting-next-governed-phase-post-149o-20l-7o-2k-4.md

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

- Existing CertificationRecord bound as active on hac-dell without modification; HMIC validator VALID; HATP does not activate

## Acceptance Checks

- fresh HMIC validator re-derivation on hac-dell returns VALID post-activation

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-20T11:32:47.209618+02:00
