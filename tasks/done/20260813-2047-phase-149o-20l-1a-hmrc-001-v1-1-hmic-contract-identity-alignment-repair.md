# Task Contract

## Task ID

20260813-2047-phase-149o-20l-1a-hmrc-001-v1-1-hmic-contract-identity-alignment-repair

## Title

Phase 149O.20L.1A: HMRC-001 v1.1 HMIC Contract-Identity Alignment Repair

## Status

done

## Mode

implementation

## Goal

Repair B-149O.20L.1-1: correct HMIC-001's stale Depends-on header line (HMRC-001 v1.0 -> v1.1) after 149O.20L.1 amended HMRC-001, without touching HMRC-001 bytes, Class-B verifier code, or production readiness wiring.

## Allowed Files

- docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md
- tests/test_phase_149o_20l_1a_hmrc_v1_1_hmic_contract_identity_alignment_repair.py
- tasks/active/*.md
- tasks/done/*.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md
- docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md
- src/pcae/core/hatp_class_b_topology_verifier.py
- src/pcae/core/hatp_environment_lock_verifier.py
- src/pcae/core/hatp_class_b_conformance.py
- src/pcae/core/hatp_mandatory_cutover.py
- src/pcae/core/hatp_mandatory_certification.py


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

- HMIC-001's Depends-on header line correctly states HMRC-001 v1.1, HMIC-001 stays v1.3 (same-version repair)
- HMRC-001 bytes byte-unchanged
- No production source file modified
- New test module passes; fast_green clean-deselected citation 0 failed

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-13T20:47:04.244565+02:00
