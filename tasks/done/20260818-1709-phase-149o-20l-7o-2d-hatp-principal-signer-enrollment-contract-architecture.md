# Task Contract

## Task ID

20260818-1709-phase-149o-20l-7o-2d-hatp-principal-signer-enrollment-contract-architecture

## Title

Phase 149O.20L.7O.2D: HATP Principal/Signer Enrollment Contract Architecture

## Status

done

## Mode

documentation

## Goal

Design (architecture-only) the missing HATP Principal/Signer Enrollment contract (new companion contract HPSE-001) resolving principal_id/signer_key_id/provider_profile semantics, plus a narrow HBDC-001 authority_scope vocabulary amendment (v1.1->v1.2, new section 16.2). No implementation, no enrollment, no DeploymentBinding creation, no election, no CHGR, no certification, no Dell mutation.

## Allowed Files

- docs/PHASE_149O_20L_7O_2D_HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT_ARCHITECTURE.md
- docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md
- docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md
- tests/test_phase_149o_20l_7o_2d_hatp_principal_signer_enrollment_contract_architecture.py
- tasks/active/20260818-1634-idle-awaiting-next-governed-phase-post-149o-20l-7o-2c.md
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

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-18T17:09:11.139988+02:00
