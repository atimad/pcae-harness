# Task Contract

## Task ID

20260814-0200-phase-149o-20l-2-full-hbdc-readiness-contract-schema-independent-verification

## Title

Phase 149O.20L.2: Full-HBDC Readiness Contract / Schema Independent Verification

## Status

active

## Mode

validation

## Goal

Independently verify HMRC-001 v1.1's Full-HBDC readiness contract/schema evolution performed in Phase 149O.20L.1, from fixed git history and current live source, trusting none of L.1's report/tests/classification. Verification-only: no production, contract, HBDC, or Class-B change.

## Allowed Files

- tests/test_phase_149o_20l_2_full_hbdc_readiness_contract_schema_independent_verification.py
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

2026-08-14T02:00:58.402459+02:00
