# Task Contract

## Task ID

20260813-2247-phase-149o-20l-1b-hmrc-001-v1-1-hmic-contract-identity-alignment-independent-verification

## Title

Phase 149O.20L.1B: HMRC-001 v1.1 HMIC Contract-Identity Alignment Independent Verification

## Status

done

## Mode

validation

## Goal

Independently verify Phase 149O.20L.1A's repair of B-149O.20L.1-1 (HMIC-001's stale Depends-on header line) without trusting L.1A's report, tests, Outcome-B classification, or historical-test attribution. Verification-only: no production, contract, or HBDC change.

## Allowed Files

- tests/test_phase_149o_20l_1b_hmrc_v1_1_hmic_contract_identity_alignment_independent_verification.py
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

- docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md
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

TBD

## Forbidden Changes

- TBD

## Acceptance Criteria

- TBD

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-13T22:47:13.011792+02:00
