# Task Contract

## Task ID

20260820-0954-phase-149o-20l-7o-2k-3-hatp-hmic-certificationrecord-real-host-creation-source-parity-revalidated

## Title

Phase 149O.20L.7O.2K.3: HATP HMIC CertificationRecord Real-Host Creation -- Source-Parity Revalidated

## Status

active

## Mode

implementation

## Goal

Execute exactly one governed narrow real-effect phase: create-only HMIC CertificationRecord on hac-dell via scripts/hatp_certification_admin.py create, source-parity revalidated fresh, no activation, no binding, no other protected-state change

## Allowed Files

- docs/PHASE_149O_20L_7O_2K_3_HATP_HMIC_CERTIFICATIONRECORD_REAL_HOST_CREATION_SOURCE_PARITY_REVALIDATED.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/done/20260820-0615-idle-awaiting-next-governed-phase-post-149o-20l-7o-2k-2.md
- tasks/active/20260820-0954-phase-149o-20l-7o-2k-3-hatp-hmic-certificationrecord-real-host-creation-source-parity-revalidated.md
- tests/test_phase_149o_20l_7o_2k_3_hatp_hmic_certificationrecord_real_host_creation_source_parity_revalidated.py
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

strict

## Forbidden Changes

- TBD

## Acceptance Criteria

- Exactly one CertificationRecord created on hac-dell; no activation/binding; no other protected-state mutation

## Acceptance Checks

- fast_green

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-20T09:54:57.024479+02:00
